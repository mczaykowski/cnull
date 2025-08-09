import numpy as np
from cnull.bench_v3 import run_once

def test_positive_directionality_smoke():
    res_on  = run_once(T=200, k_lags=3, surrogates=10, block=50, null_block=25, gamma=0.6, seed=0, echo=True,  wm_amp=0.1)
    res_off = run_once(T=200, k_lags=3, surrogates=10, block=50, null_block=25, gamma=0.6, seed=0, echo=False, wm_amp=0.1)
    assert res_on["TE_C2B"] > res_on["TE_B2C"]
    assert abs(res_off["TE_C2B"] - res_off["TE_B2C"]) < 0.1
