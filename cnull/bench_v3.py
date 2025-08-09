import os, csv
import numpy as np
from math import log
from typing import Tuple, List

def set_seed(seed: int):
    np.random.seed(seed)

def ridge_fit(X: np.ndarray, y: np.ndarray, lam: float = 1e-3):
    Xb = np.c_[X, np.ones((X.shape[0], 1))]
    I = np.eye(Xb.shape[1]); I[-1, -1] = 0.0
    W = np.linalg.pinv(Xb.T @ Xb + lam * I) @ (Xb.T @ y)
    yhat = Xb @ W
    resid = y - yhat
    var = np.var(resid)
    return W, var

def gaussian_te(source: np.ndarray, target: np.ndarray, k_lags: int = 3):
    T = len(target)
    if T < k_lags + 2:
        return 0.0, 0.0, 0.0
    idx = np.arange(k_lags, T-1)
    y = target[idx+1]
    Xb = np.column_stack([target[idx - l] for l in range(k_lags)])
    Xs = np.column_stack([source[idx - l] for l in range(k_lags)])
    _, var_b = ridge_fit(Xb, y, lam=1e-3)
    Xbf = np.column_stack([Xb, Xs])
    _, var_f = ridge_fit(Xbf, y, lam=1e-3)
    var_y = np.var(y) + 1e-12
    R2_b = 1.0 - (var_b / var_y)
    R2_f = 1.0 - (var_f / var_y)
    te = 0.5 * np.log((var_b + 1e-12) / (var_f + 1e-12))
    return float(te), float(R2_b), float(R2_f)

def circular_shift(x: np.ndarray, shift: int) -> np.ndarray:
    s = shift % len(x)
    if s == 0: return x.copy()
    return np.concatenate([x[-s:], x[:-s]])

def block_shuffle_align(src: np.ndarray, block: int) -> np.ndarray:
    n = len(src)
    if block <= 1:
        idx = np.random.permutation(n); return src[idx]
    m = (n // block) * block
    tail = src[m:]
    arr = src[:m].reshape(-1, block)
    perm = np.random.permutation(arr.shape[0])
    y = arr[perm].reshape(-1)
    if len(tail) > 0: y = np.concatenate([y, tail])
    return y

def gen_pair(T: int, gamma: float, echo: bool, wm_amp: float, seed: int):
    set_seed(seed)
    eC = np.random.randn(T); eB = np.random.randn(T)
    C = np.zeros(T); B = np.zeros(T)
    seg = max(50, T // 10)
    wm_bits = np.repeat(np.random.randint(0, 2, size=(T // seg + 1)), seg)[:T]
    wm_signal = (wm_bits * 2 - 1) * wm_amp
    for t in range(1, T):
        C[t] = 0.6 * C[t-1] + eC[t] + wm_signal[t]
        if echo:
            B[t] = 0.6 * B[t-1] + gamma * C[t-1] + eB[t]
        else:
            B[t] = 0.6 * B[t-1] + eB[t]
    C = (C - C.mean()) / (C.std() + 1e-8)
    B = (B - B.mean()) / (B.std() + 1e-8)
    return C, B, wm_bits

def decode_watermark(series: np.ndarray, bits: np.ndarray) -> float:
    x = series; T = len(x); seg = max(50, T // 10); nseg = T // seg
    if nseg == 0: return 0.5
    preds, labs = [], []
    for i in range(nseg):
        a = i*seg; b = a+seg
        m = x[a:b].mean()
        preds.append(1 if m > 0 else 0)
        labs.append(int(round(bits[a:b].mean())))
    preds = np.array(preds); labs = np.array(labs)
    return float((preds == labs).mean()) if len(labs) else 0.5

def run_once(T: int, k_lags: int, surrogates: int, block: int, null_block: int,
             gamma: float, seed: int, echo: bool, wm_amp: float):
    C, B, bits = gen_pair(T, gamma, echo, wm_amp, 10_000*seed + int(gamma*1000))
    te_c2b, R2b_base, R2b_full = gaussian_te(C, B, k_lags)
    te_b2c, R2c_base, R2c_full = gaussian_te(B, C, k_lags)
    circ_nulls_c2b, circ_nulls_b2c = [], []
    for _ in range(surrogates):
        sh = np.random.randint(k_lags+1, len(C)-k_lags-1)
        Cc = circular_shift(C, sh); Bb = circular_shift(B, sh)
        t1,_,_ = gaussian_te(Cc, B, k_lags); t2,_,_ = gaussian_te(Bb, C, k_lags)
        circ_nulls_c2b.append(t1); circ_nulls_b2c.append(t2)
    nb = null_block if null_block>0 else block
    block_nulls_c2b, block_nulls_b2c = [], []
    for _ in range(surrogates):
        Cb = block_shuffle_align(C, nb); Bb = block_shuffle_align(B, nb)
        t1,_,_ = gaussian_te(Cb, B, k_lags); t2,_,_ = gaussian_te(Bb, C, k_lags)
        block_nulls_c2b.append(t1); block_nulls_b2c.append(t2)
    def zscore(val, arr):
        a = np.array(arr); return (val - a.mean()) / (a.std() + 1e-9)
    z_circ_c2b = zscore(te_c2b, circ_nulls_c2b); z_circ_b2c = zscore(te_b2c, circ_nulls_b2c)
    z_block_c2b = zscore(te_c2b, block_nulls_c2b); z_block_b2c = zscore(te_b2c, block_nulls_b2c)
    dR2_in  = R2b_full - R2b_base
    dR2_out = R2c_full - R2c_base
    acc_in  = decode_watermark(B, bits)
    acc_out = decode_watermark(C, bits)
    return {
        "TE_C2B": te_c2b, "TE_B2C": te_b2c,
        "z_circ_C2B": z_circ_c2b, "z_circ_B2C": z_circ_b2c,
        "z_block_C2B": z_block_c2b, "z_block_B2C": z_block_b2c,
        "dR2_in": dR2_in, "dR2_out": dR2_out,
        "acc_in": acc_in, "acc_out": acc_out,
    }

def ensure_dir(p: str): os.makedirs(p, exist_ok=True)

def append_csv(path: str, header: List[str], row: List):
    exists = os.path.exists(path) and os.path.getsize(path) > 0
    with open(path, "a", newline="") as f:
        import csv
        w = csv.writer(f)
        if not exists: w.writerow(header)
        w.writerow(row)

def run_v3(out, seeds, cycles, steps, surrogates, gammas, block, lags, no_feedback, use_gaussian_te, wm_direct, wm_amp, null_block):
    ensure_dir(out)
    path_delta = os.path.join(out, "v3_TE_delta.csv")
    path_both  = os.path.join(out, "v3_TE_bothdirs.csv")
    path_wmd   = os.path.join(out, "v3_watermark_direct.csv")
    path_dr2in = os.path.join(out, "v3_dR2_in.csv")
    path_dr2out= os.path.join(out, "v3_dR2_out.csv")
    h_delta = ["segment","gamma","seed","lag","dTE","dZ_block","dZ_circ","TE_C2B","TE_B2C","z_block_C2B","z_block_B2C"]
    h_both  = ["segment","gamma","seed","lag","direction","TE","z_block"]
    h_wmd   = ["segment","gamma","seed","acc_in","acc_out"]
    h_dr2   = ["segment","gamma","seed","lag","dR2"]
    segs = [("OFF", False), ("ON", True)]
    for seg_name, echo in segs:
        for g in gammas:
            for s in range(seeds):
                res = run_once(T=cycles, k_lags=lags, surrogates=surrogates,
                               block=block, null_block=null_block,
                               gamma=g, seed=s, echo=echo, wm_amp=wm_amp)
                for L in range(1, lags+1):
                    dTE = res["TE_C2B"] - res["TE_B2C"]
                    dZb = res["z_block_C2B"] - res["z_block_B2C"]
                    dZc = res["z_circ_C2B"] - res["z_circ_B2C"]
                    append_csv(path_delta, h_delta, [seg_name, g, s, L, dTE, dZb, dZc,
                                                     res["TE_C2B"], res["TE_B2C"],
                                                     res["z_block_C2B"], res["z_block_B2C"]])
                    append_csv(path_both, h_both,  [seg_name, g, s, L, "C2B", res["TE_C2B"], res["z_block_C2B"]])
                    append_csv(path_both, h_both,  [seg_name, g, s, L, "B2C", res["TE_B2C"], res["z_block_B2C"]])
                    append_csv(path_dr2in, h_dr2,  [seg_name, g, s, L, res["dR2_in"]])
                    append_csv(path_dr2out,h_dr2,  [seg_name, g, s, L, res["dR2_out"]])
                append_csv(path_wmd, h_wmd, [seg_name, g, s, res["acc_in"], res["acc_out"]])
                print(f"[OK] {seg_name} gamma={g:.2f} seed={s} | TE C→B={res['TE_C2B']:.3f} B→C={res['TE_B2C']:.3f} | zΔ_block={dZb:.3f}", flush=True)
    print(f"Done. Outputs in: {out}")
    print("Files: v3_TE_delta.csv, v3_TE_bothdirs.csv, v3_watermark_direct.csv, v3_dR2_in.csv, v3_dR2_out.csv")
