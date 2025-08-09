import os, json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def make_figs(outdir: str):
    d = pd.read_csv(os.path.join(outdir, "v3_TE_delta.csv"))
    w = pd.read_csv(os.path.join(outdir, "v3_watermark_direct.csv"))
    gcols = ["segment","gamma"]
    m = d.groupby(gcols, as_index=False).agg(
        dTE_mean=("dTE","mean"),
        dTE_se=("dTE", lambda x: x.std(ddof=1)/np.sqrt(len(x))),
        dZb_mean=("dZ_block","mean"),
        dZb_se=("dZ_block", lambda x: x.std(ddof=1)/np.sqrt(len(x)))
    )
    # Δz_block vs gamma
    plt.figure()
    for seg in ["OFF","ON"]:
        mm = m[m.segment==seg].sort_values("gamma")
        plt.errorbar(mm["gamma"], mm["dZb_mean"], yerr=mm["dZb_se"], marker="o", label=seg)
    plt.axhline(0, linestyle="--", linewidth=1)
    plt.xlabel("gamma (dose)"); plt.ylabel("Δz_block = z(C→B) − z(B→C)")
    plt.legend(); plt.tight_layout()
    plt.savefig(os.path.join(outdir, "fig_dZblock_vs_gamma.png"), dpi=160)

    # ΔTE vs gamma
    plt.figure()
    for seg in ["OFF","ON"]:
        mm = m[m.segment==seg].sort_values("gamma")
        plt.errorbar(mm["gamma"], mm["dTE_mean"], yerr=mm["dTE_se"], marker="o", label=seg)
    plt.axhline(0, linestyle="--", linewidth=1)
    plt.xlabel("gamma (dose)"); plt.ylabel("ΔTE = TE(C→B) − TE(B→C)")
    plt.legend(); plt.tight_layout()
    plt.savefig(os.path.join(outdir, "fig_dTE_vs_gamma.png"), dpi=160)

    # watermark
    ww = w.groupby(["segment"], as_index=False).agg(acc_in=("acc_in","mean"), acc_out=("acc_out","mean"))
    plt.figure()
    plt.bar(ww["segment"], ww["acc_in"])
    plt.ylim(0,1); plt.ylabel("Watermark decode accuracy at B (received)")
    plt.tight_layout()
    plt.savefig(os.path.join(outdir, "fig_watermark_acc.png"), dpi=160)

    # verdict
    on = m[(m.segment=="ON") & (m.gamma>0.0)]
    off = m[(m.segment=="OFF")]
    verdict = {
        "delta_z_block_ON_mean": float(on["dZb_mean"].mean()) if len(on) else None,
        "delta_z_block_OFF_mean": float(off["dZb_mean"].mean()) if len(off) else None,
        "passes": bool(
            (len(on)>0) and
            (on["dZb_mean"].mean() > 5.0) and
            (abs(off["dZb_mean"].mean()) < 2.0) and
            (w[w.segment=="ON"]["acc_in"].mean() > 0.7) and
            (0.4 < w[w.segment=="OFF"]["acc_in"].mean() < 0.6)
        )
    }
    with open(os.path.join(outdir, "verdict.json"), "w") as f:
        json.dump(verdict, f, indent=2)
    return verdict
