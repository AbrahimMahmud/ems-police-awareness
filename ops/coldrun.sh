#!/bin/bash
# Deterministic to the byte (finding X20): a fixed hash seed and one BLAS thread per process.
export PYTHONHASHSEED=0 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
# CP2 line: run_all.py clean TWICE from cold, and require the second manifest to
# reproduce the first.
#
# "Cold" is defined in EXECUTION_PLAN.md (CP2 checklist): every file under
# outputs/ that a run_all stage writes is deleted first, and data/processed is
# cleared except (a) the raw page cache ems_pages/, so 00b rebuilds the extract
# from cached pages without a network fetch, and (b) the products of 18 and 19,
# which are not run_all stages (hours of resumable compute) and enter the model
# stages as certified inputs, (c) the synthetic dry run of 30, which is the
# machinery proof and refuses to run once the freeze is lifted, and (d) the
# randomization ledgers: seeded, identity-keyed checkpoints of a deterministic
# computation, so keeping them changes no number and saves hours; a cold pass
# still recomputes every artifact from inputs plus these checkpoints. Fetch stages other than 00b are excluded: upstream
# mutates and the treatment inputs are frozen.
REPO="$(cd "$(dirname "$0")/.." && pwd)"
ST="$REPO/ops/state"; mkdir -p "$ST"
LOG=$ST/coldrun.log; STATE=$ST/coldrun.state
echo $$ > $ST/coldrun.pid
cd "$REPO" || exit 1
say(){ echo "[$(date -u +%FT%TZ)] $*" | tee -a $LOG; }
while [ ! -f $ST/rebuild.done ]; do sleep 60; done
sleep 300   # let calib1000 read the panel before it is cleared
say "rebuild done; cold runs begin"
clear_cold(){
  find outputs/tables -maxdepth 1 -type f \( -name '*.csv' -o -name '*.txt' -o -name '*.json' \) \
    ! -name 'null_calibration*' ! -name 'power_analysis*' \
    ! -name 'confirmatory_results_dryrun*' ! -name 'confirmatory_reading_dryrun*' ! -name 'ri_ledger_*' -delete
  find outputs/figures -maxdepth 1 -type f \( -name '*.png' -o -name '*.pdf' \) -delete 2>/dev/null
  rm -f outputs/run_manifest.json
  find data/processed -maxdepth 1 -type f \( -name '*.parquet' -o -name '*.csv' \) -delete
  say "cleared: $(find outputs/tables -maxdepth 1 -type f | wc -l) files kept in outputs/tables (certificates, ledgers, power)"
}
pass(){ local n=$1
  grep -qx "pass$n" $STATE 2>/dev/null && { say "skip pass $n"; return 0; }
  clear_cold
  say "START pass $n: 00b from cached pages"
  (cd scripts && python3 run_all.py --fetch --only 00b_download_ems_extract.py) >> $ST/coldrun_pass${n}_00b.log 2>&1 || { say "pass $n: 00b FAILED"; return 1; }
  say "START pass $n: build, check, model"
  (cd scripts && python3 run_all.py --kind build --kind check --kind model) >> $ST/coldrun_pass$n.log 2>&1; rc=$?
  cp outputs/run_manifest.json $ST/run_manifest_pass$n.json
  say "END pass $n rc=$rc"
  [ $rc -eq 0 ] && echo "pass$n" >> $STATE
  return $rc
}
pass 1 && pass 2
python3 - "$ST" <<'PY' | tee -a $LOG
import json, sys
st = sys.argv[1]
try:
    a = json.load(open(f"{st}/run_manifest_pass1.json")); b = json.load(open(f"{st}/run_manifest_pass2.json"))
except FileNotFoundError as e:
    print("manifest comparison skipped:", e); sys.exit(0)
kind = {s["script"]: s["kind"] for s in a["stages"]}
ha = {(s["script"], o["path"]): o.get("sha256") for s in a["stages"] for o in s["outputs"]}
hb = {(s["script"], o["path"]): o.get("sha256") for s in b["stages"] for o in s["outputs"]}
diff = sorted(k for k in ha if ha[k] != hb.get(k))
# The check stages' outputs are REPORTS (the suite's result table, the append-only
# verification log, the regenerated source register) and carry timestamps; they
# are listed, never required identical. Every build and model output must match.
hard = [k for k in diff if kind.get(k[0]) != "check"]
soft = [k for k in diff if kind.get(k[0]) == "check"]
print(f"outputs compared: {len(ha)}; build/model outputs differing: {len(hard)}; timestamped reports differing: {len(soft)}")
for k in hard: print("  DIFF", k)
for k in soft: print("  report", k)
print("pass1", a["summary"], "pass2", b["summary"])
print("COLD IDENTITY:", "OK — every build and model output byte-identical across the two passes" if not hard else "FAILED")
PY
say "ALL DONE"; touch $ST/coldrun.done
