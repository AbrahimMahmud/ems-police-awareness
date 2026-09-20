#!/bin/bash
# Deterministic to the byte (finding X20): a fixed hash seed and one BLAS thread per process.
export PYTHONHASHSEED=0 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
# Phase I: the sealed one-shot confirmatory run, then its mechanical reading.
#
# Preconditions are CHECKED, not assumed: config.FREEZE_ACTIVE must be False
# (the lift commit), and no sealed result may exist yet (30 refuses to
# overwrite one). 30 is resumable through its per-cell identity-keyed ledgers,
# so a container restart mid-run loses nothing: relaunch this script. A seal
# refusal (exit 3) is a real condition — a missing certificate, a broken
# partition — and is NOT retried; only a crash or a kill is.
REPO="$(cd "$(dirname "$0")/.." && pwd)"
ST="$REPO/ops/state"; mkdir -p "$ST"
LOG=$ST/phase_i.log
echo $$ > $ST/phase_i.pid
cd "$REPO/scripts" || exit 1
say(){ echo "[$(date -u +%FT%TZ)] $*" | tee -a $LOG; }
python3 -c "from config import FREEZE_ACTIVE; raise SystemExit(0 if FREEZE_ACTIVE is False else 1)" \
  || { say "FREEZE_ACTIVE is not False; Phase I does not start"; exit 1; }
if [ ! -f "$REPO/data/reference/confirmatory_results.csv" ]; then
  for i in $(seq 1 30); do
    say "START 30_confirmatory_run try $i"
    python3 30_confirmatory_run.py --jobs "${PHASE_I_JOBS:-4}" >> $ST/step_phase_i_30.log 2>&1; rc=$?
    say "END 30_confirmatory_run rc=$rc"
    [ $rc -eq 0 ] && break
    [ $rc -eq 3 ] && { say "seal refused; not retried — read $ST/step_phase_i_30.log"; exit 3; }
    sleep 30
  done
  [ -f "$REPO/data/reference/confirmatory_results.csv" ] || { say "no sealed result after 30 tries"; exit 1; }
else
  say "sealed result already exists; not re-run"
fi
say "START 34_confirmatory_reading"
python3 34_confirmatory_reading.py >> $ST/step_phase_i_34.log 2>&1; rc=$?
say "END 34_confirmatory_reading rc=$rc"
[ $rc -eq 0 ] && touch $ST/phase_i.done
exit $rc
