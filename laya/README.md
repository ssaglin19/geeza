# Laya — System 1 fine-tuning plan

Reference: https://github.com/NandhaKishorM/laya (Apache 2.0, 322–421M
encoders, RLCD-trained, non-autoregressive typed decisions).

Hard facts from the upstream README that shape everything below:

- **Zero-shot it is near chance on typed decisions** (0.36 vs 0.32 random).
  The published numbers exist only after domain fine-tuning. We must fine-tune.
- **It ships over-confident** (ECE 0.466 until temperature-fitted per domain;
  0.081 after). Confidence bands are meaningless until calibration is fitted.
- The `score` primitive is weakest; we use `choice` and `noul` only.
- Fine-tuning runs on a free Kaggle/Colab T4 in hours — no Mac, no purchase.

## Pipeline (M1: scam screen first)

1. **Data.** Public corpora: Nazario phishing corpus, SpamAssassin public
   corpus, Enron/Enron-Spam for legitimate mail, plus synthetic scam messages
   modeled on FTC/FBI elder-fraud reports (grandparent scams, Medicare
   impersonation, utility shutoff threats, tech support). Target ≥ 20k
   examples, stratified by the five question packs in
   `questions/scam-screen.json`.
2. **Fine-tune.** The upstream repo ships a fine-tuning notebook; run per
   question pack on a free T4. Checkpoint per domain, never a general one.
3. **Calibrate.** Temperature-fit on held-out data until ECE ≤ 0.10. This step
   is not optional — every threshold in the app policy assumes calibrated
   probabilities.
4. **Report metrics.** Recall ≥ 0.95 at precision ≥ 0.90 in the act band on
   held-out elder-fraud messages. Recall is the metric: a false alarm costs a
   question to the caregiver; a miss can cost the retirement account.
5. **Export.** ONNX → Core ML via coremltools. **This step needs the Mac**
   (one-time per checkpoint). On-device target: < 50 ms per question pack
   on an A18 Neural Engine.

## Question packs in this repo

| Pack | Purpose | Primitive |
|---|---|---|
| `questions/intent-routing.json` | spoken request → skill registry (10 skills) | choice |
| `questions/scam-screen.json` | every message, before anything else | noul × 5 |
| `questions/page-guard.json` | second opinion when anchor confidence lands in confirm band | noul × 2 |

Band policy lives in the pack JSON next to the questions — the model picks,
the app routes. The model never acts.
