"""One HTTP client for every Wikimedia host, because there is one rate limit.

WHY THIS MODULE EXISTS
----------------------
Five scripts fetch from Wikimedia — 11 (pageviews), 24 (category tree), 26
(Wikidata scope), 28 (NYC attention), 29 (title resolution) — and each grew its
own retry block. They disagree, and the disagreements are not cosmetic: the
basket rebuild stalled for hours on a failure that three of the five would have
survived.

WHAT THE FAILURE ACTUALLY WAS (measured 2026-09-11, not assumed)
----------------------------------------------------------------
26_resolve_basket_scope.py's docstring said the endpoint "is currently
rate-limiting to 1 request/minute during an outage". Both halves were false, and
nobody had re-checked them:

  * There is no outage. A trivial SPARQL query answers HTTP 200 in 0.3s.
  * The limit is not per-endpoint. Wikimedia's edge (server: envoy) runs a
    token bucket keyed on the CLIENT IP and SHARED ACROSS HOSTS. In one second
    www.wikidata.org returned 200 while en.wikipedia.org returned 429 with
    Retry-After: 49; minutes later www.wikidata.org returned 429 too.
  * The server says how long to wait. Observed Retry-After values in a single
    session: 2, 5, 49, 52 seconds. 26 ignored the header and slept a fixed 70s,
    so it both over-waited on a 2s hold and under-waited on a 52s one.

Three consequences follow, and this module exists to make each impossible:

  1. HONOUR Retry-After. The server knows the refill schedule; guessing does not.
  2. PACE GLOBALLY, ACROSS PROCESSES. The bucket is per-IP, so two scripts
     running at once starve each other and neither one's backoff can see why.
     A file lock plus a shared clock makes the pacing real rather than per-run.
  3. CACHE ON THE REQUEST, NEVER ON A CALLER-SUPPLIED TAG. 26 keyed its cache
     `scope_{offset:04d}_{len(chunk)}`, so changing --batch changed every key
     and discarded every previously fetched byte — which is precisely what
     27_finalise_basket.py:129 tells a reader to do when Wikidata is refusing
     ("use --batch 50"). The claim "the cache makes it resumable" was false
     exactly when it was needed.

WHAT THIS MODULE DELIBERATELY DOES NOT DO
-----------------------------------------
It does not cache failures. A 429 is a fact about this minute, not about the
resource, and a cached 429 would turn a transient hold into a permanent absence
— the shape of the defect that made one rate-limited probe report Alton
Sterling's pre-rename title as a 404 when it held 1.86M views.

It does not swallow 404. A missing page is a fact about the world and is raised
as NotFound at once, so a caller can record "no such article" without spending
the retry budget that a transient failure deserves.

It does not touch GDELT. GDELT signals rate limiting with HTTP 200 and a
plain-text body, which can only be detected by reading the body; that stays in
11_fetch_awareness_components.py where the quirk is documented.
"""

import fcntl
import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from config import DATA_PROCESSED

# A contactable UA is Wikimedia's stated condition of use. Kept identical to the
# string the five callers already sent, so the change of client is invisible
# to the server and any per-UA behaviour stays comparable across runs.
UA = "ems-police-awareness-research/1.0 (academic; contact via repository)"

# Cross-process pacing state. The lock serialises REQUESTS, not whole scripts,
# so two stages may interleave — they simply cannot burst concurrently.
_STATE_DIR = DATA_PROCESSED / "wikimedia_state"
_LOCK = _STATE_DIR / "bucket.lock"
_CLOCK = _STATE_DIR / "bucket.json"

# Floor between consecutive requests. Wikimedia's published guidance for
# unauthenticated clients is serial requests; 0.35s is comfortably inside that
# and is what 11 already used between titles.
MIN_INTERVAL = float(os.environ.get("WIKIMEDIA_MIN_INTERVAL", "0.35"))

# Ceiling on a single honoured Retry-After. Wikimedia has never sent more than
# ~60s here; anything larger is more likely a misconfiguration than an
# instruction, and a run must not silently sleep for an hour.
MAX_SLEEP = 300.0


class NotFound(RuntimeError):
    """The resource does not exist. Permanent — never worth retrying."""


class FetchFailed(RuntimeError):
    """Transient failure that outlasted the retry budget. Retryable later."""


class ApiError(RuntimeError):
    """HTTP 200 with an {"error": ...} body — a REJECTED query, not empty data.

    Its own category because the two are indistinguishable downstream otherwise:
    29's first version reported "not dated" for all 559 titles while the API was
    answering 'rvlimit may only be used on a single page'.
    """


def _read_clock():
    try:
        return json.loads(_CLOCK.read_text())
    except Exception:
        return {"last": 0.0, "hold_until": 0.0}


def _wait_turn():
    """Block until this process may issue a request. Returns the held lock file.

    Held across the request itself, so a 429 seen by one process delays every
    other process rather than only the one unlucky enough to observe it.
    """
    _STATE_DIR.mkdir(parents=True, exist_ok=True)
    fh = open(_LOCK, "a+")
    fcntl.flock(fh, fcntl.LOCK_EX)
    while True:
        st = _read_clock()
        now = time.time()
        due = max(st.get("last", 0.0) + MIN_INTERVAL, st.get("hold_until", 0.0))
        if now >= due:
            return fh
        time.sleep(min(due - now, MAX_SLEEP))


def _release(fh, *, hold_for=0.0):
    st = _read_clock()
    st["last"] = time.time()
    if hold_for > 0:
        st["hold_until"] = max(st.get("hold_until", 0.0), time.time() + hold_for)
    try:
        _CLOCK.write_text(json.dumps(st))
    finally:
        fcntl.flock(fh, fcntl.LOCK_UN)
        fh.close()


def _retry_after(err, attempt):
    """Seconds to wait: the server's instruction, else bounded exponential."""
    try:
        hdr = float(err.headers.get("Retry-After") or 0)
    except (TypeError, ValueError):
        hdr = 0.0
    return min(hdr or min(60.0, 5.0 * 2 ** attempt), MAX_SLEEP)


def cache_path(cache_dir, key):
    return Path(cache_dir) / f"{key}.json"


def _key_for(url):
    """Cache key derived from the REQUEST, so no caller choice can invalidate it."""
    return hashlib.sha256(url.encode()).hexdigest()[:32]


def get_json(url, *, cache_dir=None, key=None, timeout=90, tries=8, label=""):
    """One paced, cached GET returning parsed JSON.

    `key` exists only so 24 can keep the cache it already paid for; leave it
    None and the key comes from the URL, which is the safe default.
    """
    path = None
    if cache_dir is not None:
        path = cache_path(cache_dir, key or _key_for(url))
        if path.exists():
            try:
                return json.loads(path.read_text())
            except json.JSONDecodeError:
                # A half-written cache file from a killed run. Refetch rather
                # than crash: a truncated cache must not become a permanent
                # failure for every future run.
                print(f"    cache corrupt, refetching: {path.name}", flush=True)
                path.unlink(missing_ok=True)

    last = None
    for attempt in range(tries):
        fh = _wait_turn()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                _release(fh)
                raise NotFound(url[:160]) from None
            wait = _retry_after(e, attempt) if e.code in (429, 503, 502, 504) else 5.0 * (attempt + 1)
            _release(fh, hold_for=wait if e.code in (429, 503) else 0.0)
            last = f"HTTP {e.code}"
            print(f"    {label or url[:60]}: HTTP {e.code}, waiting {wait:.0f}s "
                  f"(attempt {attempt + 1}/{tries})", flush=True)
            time.sleep(wait)
            continue
        except Exception as e:                      # timeout, reset, bad JSON
            _release(fh)
            last = f"{type(e).__name__}: {e}"
            time.sleep(min(5.0 * (attempt + 1), 60.0))
            continue
        _release(fh)
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(data))
        return data
    raise FetchFailed(f"{label or url[:120]} gave up after {tries} tries; last: {last}")


def api(host, params, *, cache_dir=None, key=None, **kw):
    """MediaWiki action API call against `host`, e.g. 'en.wikipedia.org'.

    Raises ApiError on a rejected query so it can never be mistaken for a page
    that simply holds no data.
    """
    p = {"format": "json", "action": "query", **params}
    url = f"https://{host}/w/api.php?" + urllib.parse.urlencode(p)
    d = get_json(url, cache_dir=cache_dir, key=key, **kw)
    if isinstance(d, dict) and "error" in d:
        raise ApiError(f"{host}: {d['error'].get('code')}: {d['error'].get('info')}")
    return d


def pageviews_items(title, start, end, *, cache_dir=None, **kw):
    """Daily pageview records for one EXACT title. NotFound only on a real 404.

    The distinction is load-bearing. A probe that treated every exception as 404
    reported Alton Sterling's pre-rename title as having no data when it held
    1,861,004 views and the request had merely been rate-limited — which is how
    93.5% of his attention came to be missing from the treatment index.
    """
    u = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
         "en.wikipedia/all-access/user/"
         f"{urllib.parse.quote(str(title).replace(' ', '_'), safe='')}"
         f"/daily/{start}/{end}")
    return get_json(u, cache_dir=cache_dir, label=f"pageviews {title}", **kw)["items"]


def sparql(query, *, cache_dir=None, **kw):
    """One Wikidata SPARQL query. Cached on the query text, not on a caller tag."""
    url = ("https://query.wikidata.org/sparql?"
           + urllib.parse.urlencode({"query": query, "format": "json"}))
    return get_json(url, cache_dir=cache_dir, label="wdqs", **kw)["results"]["bindings"]


def legacy_params_key(params):
    """24's original cache key, preserved so its existing cache stays valid.

    Recomputing those files would cost real rate-limit budget for bytes already
    on disk. New callers should not use this.
    """
    p = {**params, "format": "json", "action": "query"}
    return hashlib.sha256(json.dumps(p, sort_keys=True).encode()).hexdigest()[:24]
