# 3-minute screen recording — talking points

Phone recording of your screen is fine, per the brief. Rough timing below
adds to ~3 min; trim on the day rather than rushing through all of it.

## 0:00–0:40 — What you built and why (show README.md + `python main.py leaderboard`)
- "Priya asked for a weekly digest and a leaderboard. I kept it a script,
  not a platform, because she said 'I don't need a platform.'"
- Run `python main.py leaderboard --week 2025-11-17` live, point at the
  Escalations & Warranty table being separate from the ranked list —
  "Neha asked not to rank them, so they're reported but not ranked."

## 0:40–1:20 — The business number (show `memo/memo.md`)
- "While building this I checked a hunch from the email thread — customers
  saying 'I already told your colleague this.' It's real: 7.6% of tickets
  are a repeat contact on the same issue within a week."
- "At Rs 290/contact, cutting that to 5% is worth about Rs 64,000 a
  quarter at Vireo's real volume."

## 1:20–2:10 — What you used AI for, and what changed between versions
- Show `src/llm.py` briefly. "The digest's theme layer is the only LLM
  call in the whole tool — one call per week, capped at 60 sampled
  messages, so cost doesn't scale with ticket volume."
- **What changed:** "I first tried `llama-3.3-70b-versatile` on Groq —
  deprecated, 404. Switched to `gpt-oss-120b`. That one silently returned
  *empty* output at the default settings — turned out it's a reasoning
  model that was spending the entire token budget on hidden reasoning
  before ever writing the JSON answer. Fixed by lowering reasoning effort
  and raising the token cap; verified against a real week's data before
  trusting it."

## 2:10–2:45 — How you know it works (show `memo/eval_results.md`)
- "Two checks: does it hallucinate — I automatically verify every cited
  ticket number is real and in-category, across a sample of weeks — and
  is the theme actually right, which I checked by hand against the real
  messages."
- State the actual numbers once the eval run lands.

## 2:45–3:00 — What you left out and why
- "No scheduling, no UI, no auth — none of that was asked for, and a
  script that runs beats a platform nobody asked for. If this earns its
  keep, that's the natural next step."

## Prompts actually used with the coding assistant (mention 2–3, don't read the whole list)
- "Build a pandas loader that joins tickets to the agent roster and flags
  the legacy resolution-time data-quality issue I found."
- "Design an eval that catches the LLM inventing a ticket citation, not
  just 'does this theme sound right.'"
- "The digest call is returning empty JSON — debug why." (this is the
  gpt-oss reasoning-budget bug above — good moment to show a real
  debugging loop, not just a demo)
