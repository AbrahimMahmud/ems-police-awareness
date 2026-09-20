#!/bin/bash
# Deterministic to the byte (finding X20): a fixed hash seed and one BLAS thread per process.
export PYTHONHASHSEED=0 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
# CP2 line: 1000-sim calibration on all three strata, extending the 200-sim
# ledgers (same seeds per index; identity verified by the sidecar).
# Exit codes 0 and 1 are verdicts (CALIBRATED / NOT CALIBRATED); 3 is 18 refusing
# because the panel is absent (N11) — a cold pass clears data/processed for about
# two minutes before 01 rebuilds it — so each step retries 30 times, 20 s apart.
REPO="$(cd "$(dirname "$0")/.." && pwd)"
ST="$REPO/ops/state"; mkdir -p "$ST"
LOG=$ST/calib1000.log; STATE=$ST/calib1000.state
echo $$ > $ST/calib1000.pid
cd "$REPO/scripts" || exit 1
say(){ echo "[$(date -u +%FT%TZ)] $*" | tee -a $LOG; }
while [ ! -f $ST/rebuild.done ]; do sleep 60; done
say "rebuild done; starting 1000-sim calibrations"
run(){ local name=$1 tries=$2 ok=$3; shift 3
  grep -qx "$name" $STATE 2>/dev/null && { say "skip $name"; return 0; }
  for i in $(seq 1 $tries); do
    say "START $name try $i"; "$@" >> $ST/step_$name.log 2>&1; rc=$?; say "END $name rc=$rc"
    case ",$ok," in *",$rc,"*) echo "$name" >> $STATE; return 0;; esac; sleep 20
  done; say "GAVE UP $name"; return 1; }
run calib1000_C1   30 0,1 python3 18_null_calibration.py --stratum C1 --sims 1000 --draws 200
run calib1000_disc 30 0,1 python3 18_null_calibration.py --stratum discovery --sims 1000 --draws 200
run calib1000_C2   30 0,1 python3 18_null_calibration.py --stratum C2 --sims 1000 --draws 200
say "ALL DONE"; touch $ST/calib1000.done
