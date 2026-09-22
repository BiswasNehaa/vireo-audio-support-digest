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
- *Manual, full read-through (done):* every theme the digest produced for
  a real week (24 themes, 50 cited ticket_ids, 8 categories) checked by
  hand against the actual source messages. **50/50 citations valid** —
  every ticket_id was real, correctly categorized, and actually supported
  its theme. Zero hallucinations found. The one real gap: 4 tickets that
  plainly fit an already-identified theme weren't cited under it (e.g. a
  "bank shows payment, site shows no order" complaint wasn't grouped with
  the correctly-identified "UPI payment succeeded, order missing" theme,
  because it didn't say "UPI") — under-inclusion, not fabrication. Full
  write-up: `memo/eval_results.md`.
- *Automated, wider sample:* `src/eval.py` runs the same grounding check
  by script across a random sample of weeks (no human needed — it just
  compares output to input) to see if the 100% rate holds at scale.
  [PLACEHOLDER: fill in from eval_grounding_results.csv once the run
  completes — it's rate-limited by Groq's free tier and running slower
  than expected].

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

Claude Code (Sonnet 5) throughout, for the whole build: exploring the raw
CSVs to find the repeat-contact pattern and the legacy-timestamp bug,
writing and testing every module, and the eval harness. Groq's
`openai/gpt-oss-120b` (free tier) does the digest's theme-extraction
step itself — the only place an LLM call happens in the running tool.

Where it wasted time / what got thrown away: first attempt used
`llama-3.3-70b-versatile` on Groq — deprecated, 404 on every call.
Switched to `gpt-oss-120b`, which then silently returned *empty* output
at default settings (`finish_reason="length"`, blank `.content`) —
turned out it's a reasoning model spending the whole token budget on
hidden reasoning before ever writing the JSON answer. Fixed by setting
`reasoning_effort="low"` and raising `max_tokens`; verified against real
data before trusting it. Second throwaway: running the eval harness at
scale kept 429-ing on Groq's free-tier rate limit (8,000 tokens/min,
each call ~4,500 tokens) — added retry-with-backoff rather than switch
providers, since the tool's real usage (a few calls a week) never gets
close to that limit; it only showed up because eval runs many calls
back-to-back.

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

https://github.com/BiswasNehaa/vireo-audio-support-digest
