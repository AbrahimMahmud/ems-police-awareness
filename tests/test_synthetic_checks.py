"""Synthetic-data tests: the regression gate's checks that touch no data file.

Each test runs one check function of scripts/23_regression_suite.py that builds its own
synthetic inputs (planted effects, planted tables, temporary ledgers, flipped guard flags) or
reads only source code, and requires PASS. They run on a clone with no data at all, so they are
the part of the gate a fresh machine can exercise before any download:

    uv run pytest
"""
import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))


@pytest.fixture(scope="module")
def suite():
    saved = sys.argv
    sys.argv = ["23_regression_suite.py"]
    try:
        spec = importlib.util.spec_from_file_location("suite", SCRIPTS / "23_regression_suite.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
    finally:
        sys.argv = saved
    return m


CHECKS = [
    ("s_reference_day", "day -1 is the named omitted level of the event study"),
    ("s_joint_test", "the statistic is the joint Wald test on days 0-7"),
    ("s_cluster_by_date", "standard errors cluster on the date"),
    ("s_ppml_wired", "the counts arm fits and recovers a planted rate change"),
    ("s_dose_arm_wired", "the dose arm has a caller and recovers a planted dose effect"),
    ("s_ledger_identity", "checkpoint ledgers are keyed to their design and quarantined when stale"),
    ("s_placebo_relocations_reported", "the within-block shift's relocation count reaches the caller"),
    ("d_guard_can_fire", "the freeze guard rejects what it must"),
    ("d_discovery_scripts_pinned", "lifting the freeze cannot move exploratory scripts onto the sealed sample"),
    ("s_confirmatory_reading_rules", "the pre-registered reading reads 17 planted tables as its text requires"),
    ("s_calibration_can_fail", "the calibration verdict can fail (lattice KS, sim count, rate)"),
    ("s_draw_scheme_total", "every draw scheme is dispatched explicitly"),
]


@pytest.mark.parametrize("fn,desc", CHECKS, ids=[c[0] for c in CHECKS])
def test_check_passes(suite, fn, desc):
    state, detail = getattr(suite, fn)()
    assert state == "PASS", f"{fn} ({desc}): {state} — {detail}"
