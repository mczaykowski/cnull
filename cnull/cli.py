import argparse, sys
from .bench_v3 import run_v3
from .plots import make_figs

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    ap = argparse.ArgumentParser(prog="cnull", description="CNull CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    v3 = sub.add_parser("v3", help="Run positive-control (ON/OFF) benchmark")
    v3.add_argument("--seeds", type=int, default=6)
    v3.add_argument("--cycles", type=int, default=200)
    v3.add_argument("--steps", type=int, default=5)
    v3.add_argument("--surrogates", type=int, default=40)
    v3.add_argument("--gammas", type=str, default="0.0,0.2,0.4,0.6,0.8")
    v3.add_argument("--block", type=int, default=50)
    v3.add_argument("--lags", type=int, default=3)
    v3.add_argument("--no_feedback", type=int, default=1)
    v3.add_argument("--use_gaussian_te", type=int, default=1)
    v3.add_argument("--wm_direct", type=int, default=1)
    v3.add_argument("--wm_amp", type=float, default=0.15)
    v3.add_argument("--null_block", type=int, default=25)
    v3.add_argument("--out", type=str, default="v3_posctrl")

    figs = sub.add_parser("figs", help="Make figures + verdict from output dir")
    figs.add_argument("outdir", type=str, help="Output directory")

    args = ap.parse_args(argv)

    if args.cmd == "v3":
        gammas = [float(x.strip()) for x in args.gammas.split(",") if x.strip()!=""]
        run_v3(out=args.out, seeds=args.seeds, cycles=args.cycles, steps=args.steps,
               surrogates=args.surrogates, gammas=gammas, block=args.block,
               lags=args.lags, no_feedback=args.no_feedback, use_gaussian_te=args.use_gaussian_te,
               wm_direct=args.wm_direct, wm_amp=args.wm_amp, null_block=args.null_block)
    elif args.cmd == "figs":
        verdict = make_figs(args.outdir)
        print("Verdict:", verdict)
    else:
        ap.print_help()
