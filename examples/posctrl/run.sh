#!/usr/bin/env bash
set -euo pipefail
export OMP_NUM_THREADS=4 VECLIB_MAXIMUM_THREADS=4
cnull v3 --seeds 6 --cycles 200 --surrogates 40 --gammas 0.0,0.2,0.4,0.6,0.8 --lags 3 --null_block 25 --out v3_posctrl
cnull figs v3_posctrl
