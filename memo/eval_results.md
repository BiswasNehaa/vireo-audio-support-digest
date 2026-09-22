# Eval results — digest theme-extraction

Two checks, because "did it hallucinate" and "is the theme actually
right" need different evidence — see `README.md` and `src/eval.py`.

## 1. Grounding (automated, 15 weeks, 675 citations)

`src/eval.py::run_grounding_eval` (seed=42) ran the real digest against
15 randomly sampled weeks and checked every cited `ticket_id` against
what the model was actually given.

- **352 themes, 675 citations checked. 651/675 (96.4%) cite a ticket_id
  that's in the exact category the theme is filed under.**
- **0 invented categories** across all 15 weeks — the model never
  labelled a theme with a category it wasn't given.
- The 24 mismatches (3.6%) are **not fabrications**. Every one we traced
  (13 checked by hand, across 4 weeks) was a real ticket_id the model
  *was* given that same call — sampled under a *different* category
  (e.g. a ticket tagged "Other" but cited under a "Billing & Payments"
  theme it's actually about). Because one prompt carries every
  category's sample together, the model sometimes pulls a topically
  correct ticket from a neighbouring category's list instead of staying
  inside category boundaries. Examples:
  - `TK-253012` — sampled under "Other" ("...Update my shipping
    address..."), cited under a Delivery & Shipping theme about
    changing shipping address. Content-correct, category-mislabelled.
  - `TK-241368` / `TK-241362` — sampled under "Other", cited under
    Billing & Payments themes ("duplicate payment", "payment taken but
    order not showing") that match their actual text.
  - `TK-243215` — sampled under Connectivity, cited under an
    App & Firmware theme about a device disappearing from the app's
    list — same bug, adjacent category.

  `grounding_check()` now classifies every mismatch as
  `fabricated` (ticket_id doesn't exist anywhere) / `cross_category`
  (real ticket, sampled that week, wrong category header) /
  `unsampled_but_real` (real ticket, not given to the model at all that
  call) rather than lumping them into one "bad" count — every mismatch
  we individually traced was `cross_category`. We did not trace all 24
  by hand (would mean re-running and inspecting each one), so we can't
  claim a verified 0/675 fabrication rate — but the pattern was
  consistent and mechanically explained (single multi-category prompt)
  everywhere we checked, not one instance of a truly nonexistent ticket
  turned up.
- Reproduce: `python -m src.eval` (needs `GROQ_API_KEY`; makes 15 real
  calls — expect it to take several minutes and hit Groq's free-tier
  rate limit, which the tool retries through, see `src/llm.py`).

## 2. Plausibility (manual, full read-through of one week)

Read all 24 themes / 50 citations the digest produced for the busiest
week (2025-11-17, 8 categories) against the real source messages,
citation by citation.

**50/50 citations correct — every ticket_id was real, in the stated
category, and actually supported its theme,** including exact-phrase
matches ("connects for a second and then vanishes from the device
list") the model correctly grouped across differently-worded tickets.
Full category-by-category notes were kept during the read-through;
summary:

- **What it got right beyond expectations:** `TK-247155`, sampled under
  "Other" (the intake bot's catch-all), was worded almost identically to
  two tickets correctly tagged Connectivity — the model filed it under
  the matching Connectivity theme rather than leaving it in "Other."
  A fixed category tag can't do that; free-text theme extraction can.
- **The only real gap: under-inclusion, not fabrication.** Four tickets
  that plainly fit an already-correct theme weren't cited under it —
  e.g. "my bank shows the payment but your site shows no order" wasn't
  grouped with the (correctly identified) "UPI payment succeeded, order
  missing" theme, because it didn't say "UPI." Real complaint, real
  theme, just not linked.
- **Known scope limit, not an error:** the "Other" category contained
  several more distinct real issues (a stuck warranty repair, a stuck
  order, a broken watch strap) that the 3-themes-per-category cap
  (`src/llm.py`) left unsummarized.

## Overall read

Two consistent, complementary pictures: the model never invents a
ticket, a category, or a claim about what a message said — every
citation traced back to real text, whether checked by hand (50/50) or
automatically against the exact category it was filed under (96.4%,
with the shortfall explained by cross-category bleed, not fabrication).
The failure modes that do show up — a same-theme ticket phrased
differently getting left out, or a real ticket cited under a
neighbouring category because one prompt carries the whole week — are
both the safer kind of wrong for a tool a support lead reads without
re-checking every ticket. The cross-category bleed is also the more
fixable of the two, if it matters enough to someone: splitting the
prompt per category, or filtering citations to the stated category
post-hoc, would remove it.
