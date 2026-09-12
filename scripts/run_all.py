"""Run the pipeline in dependency order, and record exactly what happened.

WHY THIS EXISTS
---------------
There was no way to run this project end to end. The documented order omitted
scripts the pipeline depends on, and three artifacts cited in the docs had never
been created by anything (finding X10). "Reproducible" meant a person
remembering which of 38 scripts to run and in what order.

It also produces the run manifest, which is what makes a result traceable: the
git commit, the SHA256 of every input a stage read, the row count of every
artifact it wrote, wall time, and the stage's verdict. A number in the paper can
then be traced to the commit and the inputs that produced it, rather than to
"whatever was on disk that afternoon".

STAGE CLASSES, because they fail differently and cost differently
-----------------------------------------------------------------
  fetch     hits the network. Slow, rate-limited, and NOT byte-reproducible in
            general because upstream sources mutate. Skipped unless --fetch.
  build     deterministic local derivation. The default set.
  model     estimates something. Routed through the freeze guard.
  check     verifies. Never mutates an artifact.

A fetch stage is skipped by default rather than run, because re-fetching on every
pipeline run would re-register provenance hashes for data that did not change,
which is the noise that teaches people to ignore hash mismatches (finding X15).

FREEZE. Model stages inherit the guard from the scripts themselves - run_all does
not filter anything. What it DOES enforce is that no stage runs at all if
FREEZE_ACTIVE has been changed without CONFIRMATORY_UNLOCKED being passed
explicitly, so lifting the freeze cannot happen as a side effect of running the
pipeline.

  python run_all.py                      # build + model + check, no network
  python run_all.py --fetch              # include the network stages
  python run_all.py --from 12_build_cai  # resume from a stage
  python run_all.py --only 20_data_audit --only 23_regression_suite
  python run_all.py --dry-run            # print the plan and exit
"""

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

from config import DATA_PROCESSED, DATA_REFERENCE, FREEZE_ACTIVE, OUTPUTS_TABLES, PROJECT_ROOT

SCRIPTS = PROJECT_ROOT / "scripts"

# Dependency order. `needs` names artifacts that must exist BEFORE the stage runs
# and `writes` the artifacts it is expected to produce; both are checked, so a
# stage that silently writes nothing is caught here rather than three stages later.
STAGES = [
    # --- fetch: network, rate-limited, upstream mutates -------------------
    dict(script="09_fetch_public_data.py", kind="fetch", needs=[],
         writes=["data/reference/acs_2019_cd_demographics.csv"],
         note="ACS demographics and the legacy per-victim pageview file"),
    dict(script="10_build_victim_registry.py", kind="fetch", needs=[],
         writes=["data/reference/victim_registry.csv"],
         note="Mapping Police Violence registry"),
    # 10d was never a stage, yet 06_heterogeneity.py reads what it writes, so a
    # clean clone could run the whole pipeline and still have 06 fail on a
    # missing file. It needs no network — the raw spreadsheet is committed.
    dict(script="10d_parse_cd_demographics.py", kind="build", needs=[],
         writes=["data/processed/cd_demographics_clean.parquet"],
         note="community-district demographics, read by 06_heterogeneity"),
    dict(script="24_build_wiki_basket.py", kind="fetch", needs=["data/reference/victim_registry.csv"],
         writes=["data/reference/wiki_basket.csv"],
         note="candidate articles from the category walk"),
    dict(script="26_resolve_basket_scope.py", kind="fetch", needs=["data/reference/wiki_basket.csv"],
         writes=["data/reference/basket_scope.csv"],
         note="Wikidata death dates and country for each candidate"),
    dict(script="27_finalise_basket.py", kind="fetch", needs=["data/reference/basket_scope.csv"],
         writes=["data/reference/basket_decisions.csv"],
         note="include/exclude decision with a reason per article"),
    # 32 publishes the basket now; 27 only decides scope. Without this stage a
    # pipeline run would leave wikipedia_article_resolution.csv untouched while
    # every upstream input to it had changed.
    dict(script="32_validate_basket_construct.py", args=["--apply"], kind="fetch",
         needs=["data/reference/basket_decisions.csv"],
         writes=["data/reference/basket_construct_review.csv",
                 "data/reference/basket_strict.csv",
                 "data/reference/basket_broad.csv",
                 "data/reference/wikipedia_article_resolution.csv"],
         note="does each basket article describe POLICE violence? (B1, B2)"),
    dict(script="29_resolve_article_titles.py", kind="fetch",
         needs=["data/reference/wikipedia_article_resolution.csv"],
         writes=["data/reference/article_title_map.csv", "data/reference/rename_recovery.csv"],
         note="historical titles and first revisions (closes the rename defect)"),
    dict(script="11_fetch_awareness_components.py", kind="fetch",
         needs=["data/reference/article_title_map.csv"],
         writes=["data/reference/cai_components_daily.csv",
                 "data/reference/wiki_ext_basket_used.csv"],
         note="GDELT news/TV and the summed Wikipedia basket"),
    dict(script="11b_fetch_trends.py", kind="fetch", needs=[],
         writes=["data/reference/cai_trends_daily.csv"],
         note="Google Trends, stitched"),
    dict(script="28_build_nyc_attention.py", kind="fetch",
         needs=["data/reference/article_title_map.csv"],
         writes=["data/reference/wiki_nyc_daily.csv"],
         note="NYC-local validation exhibit; NOT a CAI-D component"),
    dict(script="00b_download_ems_extract.py", kind="fetch", needs=[],
         writes=["data/processed/ems_cd_day_calltype.parquet",
                 "data/processed/ems_cd_day_calltype_excluded.parquet",
                 "data/processed/ems_citywide_day_trends.parquet"],
         note="EMS outcome extract from the SODA API"),
    dict(script="16_bheard_exposure.py", kind="fetch", needs=[],
         writes=["data/reference/precinct_cd_crosswalk.csv",
                 "data/reference/bheard_cd_exposure.csv"],
         note="precinct->CD crosswalk and B-HEARD exposure bounds"),

    # --- build: deterministic local derivation -----------------------------
    dict(script="01_build_panel.py", kind="build",
         needs=["data/processed/ems_cd_day_calltype.parquet"],
         writes=["data/processed/panel_cd_day.parquet"],
         note="district x day analysis panel"),
    dict(script="12_build_cai.py", kind="build",
         needs=["data/reference/cai_components_daily.csv",
                "data/reference/cai_trends_daily.csv"],
         writes=["data/processed/cai_daily.parquet"],
         note="the composite attention index"),
    dict(script="02b_build_cai_lags.py", kind="build",
         needs=["data/processed/cai_daily.parquet"],
         writes=["data/processed/awareness_lags.parquet"],
         note="lag structure"),
    dict(script="13_extension_episodes.py", kind="build",
         needs=["data/processed/cai_daily.parquet"],
         writes=["data/reference/confirmation_episodes_rebuilt.csv"],
         note="episode list under the shock rule"),

    # --- check: verify before estimating -----------------------------------
    # Structural invariants run BEFORE the models, so a corrupt artifact is caught
    # before anything is estimated from it. Its `outputs` stage is deliberately
    # NOT run here: it reads outputs/tables/regression_suite.csv, which at this
    # point is still the PREVIOUS run's file. It ran early once and reported the
    # last run's failures as this run's - a stale read that looked like a result.
    dict(script="22_pipeline_check.py", kind="check",
         needs=["data/processed/panel_cd_day.parquet"],
         writes=["outputs/tables/pipeline_check.csv"],
         args=["--stage", "panel", "--stage", "treatment",
               "--stage", "episodes", "--stage", "bheard"],
         note="structural invariants (artifacts)"),
    dict(script="20_data_audit.py", kind="check", needs=[],
         writes=["outputs/tables/data_audit.csv"],
         note="data integrity audit"),
    dict(script="31_verify_sources.py", kind="check", needs=[],
         writes=["data/reference/source_verification_log.csv",
                 "docs/SOURCE_REGISTER.md"],
         args=["--offline"],
         note="registers and claims (offline; --fetch makes it a full scan)"),
    dict(script="23_regression_suite.py", kind="check", needs=[],
         writes=["outputs/tables/regression_suite.csv"],
         note="every audit finding as an executable check"),
    # Now that the suite has written this run's results, check them.
    dict(script="22_pipeline_check.py", kind="check",
         needs=["outputs/tables/regression_suite.csv"],
         writes=["outputs/tables/pipeline_check.csv"],
         args=["--stage", "outputs"],
         note="verdict on this run's suite output"),

    # --- model: estimates, freeze-guarded by the scripts themselves --------
    dict(script="17_stacked_event_study.py", kind="model",
         needs=["data/processed/panel_cd_day.parquet",
                "data/reference/confirmation_episodes_rebuilt.csv"],
         writes=['outputs/tables/event_study_results.csv', 'outputs/tables/event_study_path.csv'], note="the primary estimator"),
    dict(script="03_main_model.py", kind="model",
         needs=["data/processed/panel_cd_day.parquet"], writes=['outputs/tables/irf_main.csv', 'outputs/tables/joint_tests.csv'],
         note="distributed lag, secondary"),
    dict(script="04_robustness.py", kind="model",
         needs=["data/processed/panel_cd_day.parquet"], writes=['outputs/tables/robustness_counts_permutation.csv'], note=""),
    dict(script="05_placebo_and_calls.py", kind="model",
         needs=["data/processed/panel_cd_day.parquet"], writes=['outputs/tables/decomposition_windows.csv'],
         note="placebo outcomes reported beside the primary"),
    dict(script="06_heterogeneity.py", kind="model",
         needs=["data/processed/panel_cd_day.parquet"], writes=['outputs/tables/heterogeneity_results.csv'], note=""),
    dict(script="07_did_exposure.py", kind="model",
         needs=["data/processed/panel_cd_day.parquet"], writes=['outputs/tables/did_exposure_results.csv'], note=""),
    dict(script="08_figures.py", kind="model",
         needs=["data/processed/panel_cd_day.parquet"], writes=['outputs/figures/fig1_raw_series.png'], note="figures"),
]

KINDS = ("fetch", "build", "check", "model")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def artifact_fact(rel):
    """Existence, hash and realised row count — WITHOUT loading any values.

    Several of these artifacts contain confirmation-period outcomes. The manifest
    needs to know how many rows a stage wrote, and nothing more, so this reads
    the parquet footer and counts CSV newlines rather than parsing the data.

    That is the difference between an exemption that is declared and one that is
    true. D.guard_coverage flagged this script the first time it ran, because a
    pd.read_parquet here would have pulled confirmation-window outcome values
    into memory to compute len(). Incident F2 happened on exactly that kind of
    reasoning - "it is only metadata" - so the code is now shaped so the claim
    cannot quietly stop being true.
    """
    p = PROJECT_ROOT / rel
    if not p.exists():
        return {"path": rel, "exists": False}
    fact = {"path": rel, "exists": True, "bytes": p.stat().st_size, "sha256": sha256(p)}
    try:
        if p.suffix == ".parquet":
            import pyarrow.parquet as pq
            fact["rows"] = pq.ParquetFile(p).metadata.num_rows      # footer only
        else:
            with open(p, "rb") as f:                                # newline count only
                fact["rows"] = max(sum(1 for _ in f) - 1, 0)
    except Exception as e:
        fact["rows"] = None
        fact["read_error"] = f"{type(e).__name__}: {e}"
    return fact


def git_commit():
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT,
                           capture_output=True, text=True, timeout=20)
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=PROJECT_ROOT,
                               capture_output=True, text=True, timeout=20)
        return {"commit": r.stdout.strip(),
                "dirty": bool(dirty.stdout.strip()),
                "dirty_files": len(dirty.stdout.strip().splitlines())}
    except Exception as e:
        return {"commit": None, "error": str(e)}


def run_stage(st, timeout):
    """Run one stage. Returns a manifest entry. Never raises on stage failure."""
    name = st["script"]
    missing = [n for n in st["needs"] if not (PROJECT_ROOT / n).exists()]
    if missing:
        return {"script": name, "kind": st["kind"], "state": "BLOCKED",
                "detail": f"missing inputs: {missing}", "seconds": 0.0,
                "inputs": [], "outputs": []}

    inputs = [artifact_fact(n) for n in st["needs"]]
    cmd = [sys.executable, name] + list(st.get("args", []))
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, cwd=SCRIPTS, capture_output=True, text=True,
                              timeout=timeout)
        rc, tail = proc.returncode, (proc.stdout or "")[-1200:] + (proc.stderr or "")[-1200:]
    except subprocess.TimeoutExpired:
        rc, tail = -1, f"TIMEOUT after {timeout}s"
    dt = time.time() - t0

    outputs = [artifact_fact(w) for w in st["writes"]]
    unwritten = [o["path"] for o in outputs if not o["exists"]]
    if rc == 0 and unwritten:
        state, detail = "FAIL", f"exited 0 but did not write: {unwritten}"
    elif rc == 0:
        state, detail = "PASS", ""
    else:
        state, detail = "FAIL", f"exit {rc}"
    return {"script": name, "kind": st["kind"], "state": state, "detail": detail,
            "seconds": round(dt, 1), "inputs": inputs, "outputs": outputs,
            "tail": tail if state != "PASS" else ""}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true", help="include network stages")
    ap.add_argument("--kind", action="append", choices=KINDS,
                    help="run only these kinds (repeatable)")
    ap.add_argument("--from", dest="start", help="resume from this script name")
    ap.add_argument("--only", action="append", help="run only these scripts (repeatable)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--timeout", type=int, default=5400, help="per-stage seconds")
    ap.add_argument("--continue-on-fail", action="store_true",
                    help="keep going after a failed stage (default: stop)")
    ap.add_argument("--confirmatory-unlocked", action="store_true",
                    help="acknowledge that FREEZE_ACTIVE is False and proceed")
    args = ap.parse_args()

    # Lifting the freeze must be a deliberate act, never a side effect of running
    # the pipeline. If the flag is off and this was not passed, refuse.
    if not FREEZE_ACTIVE and not args.confirmatory_unlocked:
        print("REFUSING TO RUN: config.FREEZE_ACTIVE is False but "
              "--confirmatory-unlocked was not passed.\n"
              "The confirmation sample is open. That must be a deliberate, "
              "greppable act with the CP2 gate behind it, not a pipeline default.")
        return 2

    plan = list(STAGES)
    if not args.fetch:
        plan = [s for s in plan if s["kind"] != "fetch"]
    if args.kind:
        plan = [s for s in plan if s["kind"] in args.kind]
    if args.only:
        want = {o if o.endswith(".py") else o + ".py" for o in args.only}
        plan = [s for s in plan if s["script"] in want]
    if args.start:
        start = args.start if args.start.endswith(".py") else args.start + ".py"
        names = [s["script"] for s in plan]
        if start not in names:
            print(f"--from {start}: not in the plan. Stages: {names}")
            return 2
        plan = plan[names.index(start):]

    print(f"freeze: {'ACTIVE (discovery only)' if FREEZE_ACTIVE else 'LIFTED'}")
    print(f"plan: {len(plan)} stage(s)" + ("  [DRY RUN]" if args.dry_run else ""))
    for s in plan:
        print(f"   {s['kind']:<6} {s['script']:<36} {s['note']}")
    if args.dry_run:
        return 0

    entries, t0 = [], time.time()
    for s in plan:
        print(f"\n=== {s['kind']} {s['script']} ===", flush=True)
        e = run_stage(s, args.timeout)
        entries.append(e)
        mark = {"PASS": "  ok  ", "FAIL": " FAIL ", "BLOCKED": " ---- "}[e["state"]]
        print(f"[{mark}] {s['script']} in {e['seconds']}s {e['detail']}", flush=True)
        if e["state"] == "FAIL":
            print(e["tail"][-1500:])
            if not args.continue_on_fail:
                print("\nstopping. Pass --continue-on-fail to run the rest anyway.")
                break

    manifest = {
        "git": git_commit(),
        "freeze_active": bool(FREEZE_ACTIVE),
        "wall_seconds": round(time.time() - t0, 1),
        "stages": entries,
        "summary": {k: sum(1 for e in entries if e["state"] == k)
                    for k in ("PASS", "FAIL", "BLOCKED")},
    }
    out = PROJECT_ROOT / "outputs" / "run_manifest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2))

    print("\n" + "-" * 100)
    print(f"{len(entries)} stage(s) in {manifest['wall_seconds']}s: " +
          "  ".join(f"{k}={v}" for k, v in manifest["summary"].items() if v))
    print(f"manifest -> {out.relative_to(PROJECT_ROOT)}")
    if manifest["git"].get("dirty"):
        print(f"NOTE: working tree had {manifest['git']['dirty_files']} uncommitted "
              "file(s); this run is not attributable to a single commit.")
    return 1 if manifest["summary"]["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
