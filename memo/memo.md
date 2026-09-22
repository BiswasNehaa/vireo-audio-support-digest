# Weekly ticket digest & agent leaderboard — what it does and what it's worth

**To:** Priya Raman, Head of Customer Experience
**From:** Kabir Nanda
**Re:** The tickets thing

## What we built

A tool that reads your support ticket export and produces two things every
week: a **digest** of what customers are actually complaining about
(volume by category, what changed from the week before, and — for
categories where the category tag alone is too broad — the specific
sub-complaints inside it, in plain English, each traceable back to the
real tickets it came from), and a **leaderboard** of tickets closed per
agent per week.

It's a script you run, not a platform — you said you didn't need one, so
we didn't build one.

## The number

While building the digest, we checked a hunch from Neha's email: chat
agents sometimes hear "I already told your colleague this." It's real.
**7.6% of tickets in the 18 months we have are a customer contacting you
again about the same issue within a week of their last one on it** — a
repeat contact, not a new problem.

At the Rs 290 blended cost-per-contact you quoted Arjun, cutting that rate
from 7.6% to 5% is worth roughly **Rs 64,000 a quarter** at your stated
ticket volume (~650/week) — about Rs 2.5 lakh a year. That's the number
we'd put in front of Arjun: this isn't just a reading tool, it's pointing
at a specific, priceable leak.

*(One caveat on this number: the data pack we worked from covers roughly a
quarter of your actual weekly volume, so we measured the 7.6% rate on the
sample and scaled the rupee figure to your real volume. If the real
population's rate differs from the sample's, the number moves with it —
worth re-running once a full export is available.)*

## The leaderboard, and one change we made

You asked to see tickets closed per agent per week — you'll see that.
Neha separately asked, in the same thread, not to rank Escalations &
Warranty on raw ticket count, since their cases run for days by design and
a count-based ranking would make them look idle. We agreed and built it
that way: Warranty is reported on its own, not mixed into the ranked
table. It felt like the kind of thing worth just doing rather than asking
about — you can put them back in if you'd rather see one list.

## How we know it works

Two different checks, because "is this a good complaint summary" and "did
the tool make something up" need different kinds of evidence:

- **Did it make anything up?** Every theme in the digest cites the actual
  ticket numbers behind it. We automatically checked, across a sample of
  weeks, that every cited ticket number is real and actually belongs to
  that category — [PLACEHOLDER: citation validity rate]% of citations
  checked out.
- **Is the theme actually right?** We read a sample of the themes against
  the real messages ourselves — [PLACEHOLDER: manual accuracy] correct out
  of [PLACEHOLDER: sample size]. The kind of miss we saw: [PLACEHOLDER:
  representative failure example].

## What's still rough

- The digest reads better with an AI theme layer turned on; without an API
  key it still runs, but you only get the numbers, not the plain-English
  summary.
- The "repeat contact" number is inferred (same customer, same category,
  within 7 days) — there's no field in the export that says "this is a
  repeat." It's a reasonable proxy, not a certainty.
- We haven't automated sending this weekly — right now it's a command
  someone runs. Scheduling it is a small follow-on, not a rebuild.

Happy to walk through any of this live.
