# Vireo Audio — support ticket digest & leaderboard

A weekly complaint digest and an agent leaderboard, built from 18 months of
Vireo Audio support tickets. Built for Priya Raman's ask: "gives me a
weekly digest of what people are complaining about... and a leaderboard of
agents by tickets closed per week."

## What this actually does

- **Digest**: per category, ticket volume this week vs last week, average
  CSAT, repeat-contact rate — computed directly from the data, always
  available — plus, when an LLM key is configured, 1–3 short complaint
  *sub-themes* per category pulled from the actual customer messages (e.g.
  within "Connectivity": "drops mid-call" vs "won't pair with Android" are
  reported separately, not just lumped under "Connectivity").
- **Leaderboard**: tickets closed per agent for a given week. Escalations
  & Warranty is reported separately and left out of the ranking — their
  cases run days by design, and Neha Kulkarni (Support Ops) specifically
  asked not to rank them on raw ticket count. See `memo/memo.md`.
- **Business number**: a repeat-contact rate (7.6% of tickets, measured)
  and what closing part of that gap is worth per quarter. See
  `memo/memo.md` for the number and the reasoning.

## Setup (from a clean machine)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Put the data pack (`tickets.csv`, `agents.csv`, `orders.csv`,
`customers.csv`, `products.csv`) in `data/`. It is **not** committed to
this repo — it contains customer names and free-text messages, and the
repo is public. You already have it; it's the pack this brief shipped
with.

Optional, for the LLM theme layer: get a free key at
[console.groq.com](https://console.groq.com) and create `.env`:

```
GROQ_API_KEY=your_key_here
```

Without a key, the digest still runs — it just skips the theme narrative
and prints the deterministic stats table.

## Run

```bash
python main.py weeks                        # list available week_start dates
python main.py digest --week 2025-11-17      # weekly complaint digest
python main.py leaderboard --week 2025-11-17 # agent leaderboard
```

Both commands default to the most recent complete week if `--week` is
omitted.

## Tests

```bash
python tests/run_all.py
```

(Plain scripts, not pytest, so there's no extra dependency — each prints
`all tests passed` or raises.) `test_digest.py` and `test_eval.py` mock
the LLM call, so the suite runs with zero API calls and zero cost.

## How the theme layer is evaluated

`src/eval.py` runs the real digest against a sample of weeks and checks
that every `ticket_id` a theme cites actually belongs to the sample of
messages given to the model for that category — a hallucinated or
mismatched citation is the failure mode that matters for a tool someone
will trust without re-reading every ticket. Results and the manual
plausibility spot-check are in `memo/eval_results.md`.

## Known limitations / what's left out

See `memo/memo.md` and the submission form for the full list. Short
version: no auth/scheduling (this is a script you run, per Priya's "I
don't need a platform"), themes are evaluated for grounding not for
being the *single best* theme a human would pick, and the business-goal
number scales a rate measured on this data pack up to Vireo's stated real
volume (the pack itself covers roughly a quarter of it) — an explicit,
documented assumption, not a measurement of the full population.
