# Eval results — digest theme-extraction

Two separate checks (see `README.md` and `src/eval.py` for why they're
kept separate): grounding is automated and objective; plausibility needs
a human to read the source messages.

## 1. Grounding (automated)

`src/eval.py::run_grounding_eval` runs the real digest against a random
sample of weeks and checks every `ticket_id` a theme cites against the
actual set of messages given to the model for that category that week.

- Sample: 15 weeks, seed=42
- **Citation validity rate: [FILL IN FROM eval_grounding_results.csv]**
- Total themes / citations checked: [FILL IN]
- Invented categories: [FILL IN]

Reproduce with `python -m src.eval` (needs `GROQ_API_KEY` in `.env`;
makes 15 real API calls, one per sampled week).

## 2. Plausibility (manual, full read-through)

Read every theme the digest produced for the busiest week
(2025-11-17, 62 tickets across 8 categories) against the actual sampled
customer messages, by hand, citation by citation.

**Result: 24 themes, 50 citations checked, 0 hallucinated or
miscategorized citations.** Every single ticket_id a theme pointed to
was real, in the right category, and actually supported the stated
theme — including exact-phrase matches like "connects for a second and
then vanishes from the device list" (Connectivity) and "left side has no
audio at all" (Audio Quality) that the model correctly grouped across
multiple, differently-worded tickets. Audio Quality, Returns & Refunds,
and Connectivity had full or near-full coverage of their sampled
messages with zero errors.

**The one real failure mode found: under-inclusion, not fabrication.**
Four tickets that plainly belonged to an existing theme weren't cited
under it:
- `TK-247144` ("my bank says Rs 4999 went to you but your site says I
  have no orders") should have joined the "UPI payment shows success but
  order not reflected" theme (Billing & Payments) — same complaint,
  phrased around a bank debit instead of UPI.
- `TK-247200` ("package not delivered even after 14 days") should have
  joined "order not delivered / tracking not updating" (Delivery &
  Shipping).
- `TK-247143` and `TK-247275` (charging case dead after 6 hours;
  "dies by lunchtime with light use" — nearly identical wording to a
  ticket that *was* cited) should have joined the charging-failure and
  short-battery-life themes (Charging & Battery) respectively.

None of these are wrong statements — they're real complaints that fit a
real theme the model already correctly identified, just left uncited.
For a tool a support lead reads without re-checking every ticket, that's
the safer direction to err in (undercounting a real pattern) than the
alternative (inventing one).

**A genuinely useful catch, not a miss:** the "Other" category (the
intake bot's catch-all) contained `TK-247155` — "it connects for a
second and then vanishes from the device list" — worded almost
identically to two tickets the bot *did* tag Connectivity
(`TK-247053`, `TK-247065`). The model correctly surfaced it as the same
issue despite the bot's inconsistent tagging. That's exactly the kind of
thing a fixed category tag can't do and free-text theme extraction can.

**Known blind spot in this check:** "Other" contained several more
distinct real issues (a stuck warranty repair, a stuck order, a charging
fault, a broken watch strap) that the 3-themes-per-category cap left
unsummarized. Not an error — a scope tradeoff (see `src/llm.py`) — but
worth knowing before assuming the digest surfaces *everything* in a
noisy category.

## Overall read

Citation grounding held up perfectly on this read-through: the model
never invented a ticket, a category, or a false claim about what a
message said. The failure mode that shows up is under-inclusion — a real
complaint phrased unusually gets left out of an otherwise-correct theme,
or a low-frequency issue in a noisy category doesn't make the top-3 cut
— not hallucination. That's the direction you want a support-facing
summary tool to fail in.
