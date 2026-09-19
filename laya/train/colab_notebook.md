# Laya scam-screen fine-tune — Colab/Kaggle runbook

Free T4 is enough (Laya's own repo fine-tunes in 4–5 hr on Kaggle T4s; this
corpus is smaller). Run the cells in order.

## Cell 1 — environment

```python
!pip install -q laya
# Upload generate_scam_corpus.py and finetune.py from the repo (laya/datasets, laya/train),
# or clone the repo if it's accessible from the notebook.
```

## Cell 2 — generate the corpus

```python
!python generate_scam_corpus.py --out scam_corpus.jsonl --n-scam 800 --n-legit 800 --seed 42
```

Sanity-check the output: ~1600 records, roughly balanced, categories printed.
If a category has < 40 records, bump --n-scam.

## Cell 3 — fine-tune + temperature-fit + evaluate

```python
!python finetune.py --corpus scam_corpus.jsonl --out ./laya-scam-v1 --epochs 3
```

Read the gates. All three must pass before the checkpoint is a candidate:
recall >= 0.95, FPR <= 0.05, ECE <= 0.10. If recall passes but ECE fails,
the temperature fit didn't take — re-run with more calibration data, do NOT
lower the ECE gate.

## Cell 4 — download the checkpoint

```python
from google.colab import files
!tar czf laya-scam-v1.tar.gz laya-scam-v1/
files.download("laya-scam-v1.tar.gz")
```

## After the run

- Put `laya-scam-v1/` in `laya/checkpoints/` locally (gitignored — never commit weights).
- Record the run: date, corpus hash, metrics, in `laya/checkpoints/laya-scam-v1/RUN.md`.
- The Core ML conversion (M3, needs the Mac) targets this checkpoint.

## Known failure modes (from the Laya README — do not skip)

- Zero-shot Laya is near chance; the fine-tune is the product, not the base model.
- Calibration ships over-confident; the temperature fit is not optional.
- If per-category recall for `grandparent` or `romance` lags, those templates
  are few-shot — add real (scrubbed) examples before re-running.
