# CNull

CNull is a **directionality sanity-check** for emergent communication: it tells you if apparent coordination is just **crystallization** (pretty self-organization) or **real, directed information flow**.

It ships with a **positive control** benchmark (ON/OFF channel with dose γ), **dual surrogate nulls** (circular + block), **ΔTE** directionality, and a **watermark** sanity check. It runs locally in ~minutes and produces CSVs + plots + a `verdict.json` suitable for CI.

## Why this exists

Many “emergence” metrics light up on synchronized-but-meaningless dynamics. CNull requires **interventions** (ON/OFF) and checks **directionality** with **TE** and robust nulls. If your metric passes on the crystallization null, don't trust it.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install -e .
# macOS perf tweak (optional)
export OMP_NUM_THREADS=4 VECLIB_MAXIMUM_THREADS=4
# run positive control (ON/OFF + dose gamma)
cnull v3 --seeds 6 --cycles 200 --surrogates 40 --gammas 0.0,0.2,0.4,0.6,0.8 --lags 3 --null_block 25 --out v3_posctrl
# make plots + verdict
cnull figs v3_posctrl
```

Open:
- `v3_posctrl/fig_dZblock_vs_gamma.png`
- `v3_posctrl/fig_dTE_vs_gamma.png`
- `v3_posctrl/fig_watermark_acc.png`
- `v3_posctrl/verdict.json`

## What you get

- **ΔTE** and **Δz** (C→B minus B→C) split ON vs OFF, scaling with **γ** (dose).
- **Watermark** only decodes in ON (OFF ≈ chance).
- A simple **verdict** JSON for dashboards/CI.

## Status

- ✅ Positive control
- 🧪 LLM adapter stub (`cnull llm-adapt` soon)
- 🧪 Dashboard (Streamlit) planned
- 🧪 Nonlinear TE (kNN/PCMCI) planned

## License

Apache-2.0 © Mariusz Czajkowski
