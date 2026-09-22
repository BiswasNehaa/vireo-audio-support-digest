# Submission — Vireo Audio Support Tickets (Set A)

**What did you build, and what business outcome does it move? State the
number and the money.**

A weekly ticket digest (category volumes, week-over-week change, CSAT,
and LLM-grounded complaint sub-themes) and an agent leaderboard (tickets
closed per week, per Priya's ask, with Escalations & Warranty reported
separately per Neha's request). While building it we quantified a hunch
from the email thread: **7.6% of tickets (952 of 12,528) are a customer
re-contacting about the same issue within 7 days.** At the quoted Rs
290/contact blended cost, cutting that from 7.6% to 5% is worth roughly
**Rs 64,000/quarter (~Rs 2.5 lakh/year)** at Vireo's stated real volume
(650 tickets/week). Full reasoning in `memo/memo.md`.

**What does one run cost, and what would a month cost at Vireo's volume
(roughly 650 tickets a week)? Show the arithmetic. If you used no paid
calls, say so.**

The only LLM call in the tool is the digest's theme-extraction step — one
call per week, capped at 60 sampled messages regardless of actual ticket
volume (so the bill doesn't scale with tickets/week). Measured on a real
run: ~2,800 prompt tokens + ~1,600 completion tokens ≈ 4,400 tokens/call.
We used **Groq's free tier** (`openai/gpt-oss-120b`), so the actual cost
is **Rs 0**. At Vireo's volume that's ~4–5 digest runs/month
(~20,000 tokens/month total) — trivially inside Groq's free-tier rate
limits. Leaderboard and the deterministic stats half of the digest make
zero LLM calls. If Groq's free tier ever became unavailable, the same
prompt on a cheap paid model (e.g. Claude Haiku, roughly $1/$5 per
million input/output tokens) would cost on the order of **$0.02–$0.10 a
month** at this volume — noted for robustness, not because we needed it.

**How do you know it works? Sample size, how you checked, error rate, and
the kind of case it gets wrong.**

Two checks, because "did it hallucinate" and "is the theme actually
right" need different evidence:
- *Grounding (automated):* every theme cites the ticket_ids behind it; we
  ran the real digest against [N] sampled weeks and checked every citation
  against the actual messages given to the model. [PLACEHOLDER: citation
  validity rate] valid across [PLACEHOLDER: total citations checked].
- *Plausibility (manual):* read a sample of themes against the source
  messages ourselves. [PLACEHOLDER: X/Y correct]. Typical failure mode:
  [PLACEHOLDER — filled in after the read-through].

**Did you change, narrow, or push back on the client's ask? What, when,
and why.**

Yes, two things: (1) Escalations & Warranty is excluded from the ranked
leaderboard per Neha's email, reported separately instead — decided while
building the leaderboard, before showing anyone, because ranking them on
raw count directly contradicts what she asked for in the same thread
Priya's request came from. (2) We reframed "a weekly digest" as also
carrying one specific, priced metric (repeat-contact rate) rather than
pure prose, because Arjun's email made clear the tool needs to earn its
keep in rupees, not just be more readable than raw tickets.

**What is wrong with what you are handing us? Be specific: bugs,
shortcuts, things you know are off.**

- The digest's "repeat contact" flag is inferred (same customer + category
  within 7 days), not a real linking field — it will miss repeats that
  change category, and could over-count coincidental unrelated issues
  within the window.
- No scheduling/delivery — it's a command you run, not an email that
  arrives Monday morning.
- Legacy (pre-14-Sep-2025) tickets: ~60% of them have a resolved_at
  earlier than created_at (negative resolution time) — a migration
  artifact per the email thread. We flag these rather than silently
  dropping or fixing them, but resolution-time-based stats for that
  period should be read with that in mind.
- We did not have `support-policy.pdf` when building the cost/SLA
  assumptions — the Rs 290/contact figure and the "650 tickets/week"
  volume are both taken from the email thread, not the policy doc itself.
- [PLACEHOLDER: anything else found while finishing up]

**What did you deliberately leave out, and why that rather than
something else?**

No scheduling/email delivery, no web UI, no auth — Priya explicitly said
"I don't need a platform," so a runnable script beats infrastructure no
one asked for. We also didn't build anomaly detection or a full NL-query
interface over the tickets (both natural extensions of this data) because
the two things actually asked for — digest and leaderboard — weren't done
yet, and finishing those properly mattered more than breadth.

**Anything you built or found that nobody asked for?**

The repeat-contact metric itself — Neha's email raised it as an
unconfirmed hunch ("might just be the usual noise, I haven't checked"),
not a request for a metric. We checked it and it turned out to be the
strongest, most priceable finding in the data pack.

**What did you use AI for? Which tools and models, where they helped,
where they wasted your time, what you threw away. Link your
three-minute screen recording here.**

[PLACEHOLDER — see memo and fill in after recording: coding assistant
used throughout for the pipeline (data joins, the digest/leaderboard
logic, the eval harness); Groq's `openai/gpt-oss-120b` for the digest's
theme-extraction step itself. Thrown away: an earlier attempt at
`llama-3.3-70b-versatile` (deprecated on Groq's API, 404) and the default
reasoning effort on gpt-oss-120b, which silently returned empty output
because reasoning consumed the whole token budget before the JSON answer
— fixed by lowering reasoning effort and raising the token cap.]

Screen recording: [PLACEHOLDER]

**Your Public Google Drive Link**

[PLACEHOLDER]

**Someone picks this up on Monday and you are unreachable. The three
things they need to know.**

1. The business number (repeat-contact rate → Rs/quarter) is scaled from
   a sample: this data pack covers ~160 tickets/week measured against
   Vireo's stated real 650/week, so the rate is measured on ~25% of real
   volume and then priced at full volume. Re-run `src/metrics.py` against
   a full export before quoting the number externally again.
2. The digest's theme narrative needs a Groq API key in `.env`
   (`GROQ_API_KEY=`) to produce anything beyond the stats table — without
   one it degrades silently to stats-only, by design, not a bug.
3. Escalations & Warranty is intentionally excluded from the leaderboard
   ranking (`src/leaderboard.py:EXCLUDE_FROM_RANKING`) — if Priya wants
   them back in, that's a one-line change, not a rebuild.

**Honest hours spent. One number.**

[PLACEHOLDER]

**Github Repo Link**

[PLACEHOLDER]
