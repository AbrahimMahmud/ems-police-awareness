#!/bin/bash
# Deterministic to the byte (finding X20): a fixed hash seed and one BLAS thread per process.
export PYTHONHASHSEED=0 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
# Restart-tolerant rebuild of every outcome-side artifact, in dependency order.
# Relaunch after any restart: completed steps are skipped; 17 and 18 resume
# from their identity-verified ledgers.
REPO="$(cd "$(dirname "$0")/.." && pwd)"
ST="$REPO/ops/state"; mkdir -p "$ST"
LOG=$ST/rebuild.log; STATE=$ST/rebuild.state
echo $$ > $ST/rebuild.pid
cd "$REPO/scripts" || exit 1
say(){ echo "[$(date -u +%FT%TZ)] $*" | tee -a $LOG; }
run(){ # run NAME MAXTRIES OKCODES -- cmd...
  local name=$1 tries=$2 ok=$3; shift 3
  grep -qx "$name" $STATE 2>/dev/null && { say "skip $name (done)"; return 0; }
  for i in $(seq 1 $tries); do
    say "START $name try $i: $*"
    "$@" >> $ST/step_$name.log 2>&1; rc=$?
    say "END   $name rc=$rc"
    case ",$ok," in *",$rc,"*) echo "$name" >> $STATE; return 0;; esac
    sleep 15
  done
  say "GAVE UP $name"; return 1
}
run fetch_ems    6 0   python3 00b_download_ems_extract.py
run panel        3 0   python3 01_build_panel.py
run coverage35   3 0   python3 35_coverage_breaks.py
run calib_disc   6 0,1 python3 18_null_calibration.py --stratum discovery --sims 200 --draws 200
run calib_C1     6 0,1 python3 18_null_calibration.py --stratum C1 --sims 200 --draws 200
run es_500       6 0   python3 17_stacked_event_study.py --draws 500
run decomp       3 0   python3 05_placebo_and_calls.py
run main03       3 0   python3 03_main_model.py
run robust04     3 0   python3 04_robustness.py
run hetero06     3 0   python3 06_heterogeneity.py
run did07        3 0   python3 07_did_exposure.py
run figs08       3 0   python3 08_figures.py
run antipolice33 3 0   python3 33_antipolice_sensitivity.py
run calib_C2     6 0,1 python3 18_null_calibration.py --stratum C2 --sims 200 --draws 200
run power19      6 0   python3 19_power.py
say "ALL DONE"; touch $ST/rebuild.done
