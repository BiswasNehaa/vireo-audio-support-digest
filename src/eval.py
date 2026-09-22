"""Evaluate the digest's LLM theme-extraction step.

There's no ground-truth "correct theme" label in this data, so quality is
split into two checks that need different kinds of evidence:

1. Grounding (automated, objective, run on many weeks): every ticket_id a
   theme cites must actually be one of the messages we gave the model for
   that category that week. This is the failure mode that actually
   matters for a tool a support lead will trust -- a theme that cites a
   ticket that doesn't support it (or doesn't exist) is a hallucination,
   and it's fully checkable by comparing output to input, no human needed.
2. Plausibility (human judgement, small sample): does the theme actually
   describe what's in the cited messages, in a way a human reading the
   same messages would agree with? That needs a person to read messages
   and rate -- see eval_results.md for the manually-scored sample.
"""
from __future__ import annotations

import random

import pandas as pd

from src.digest import _sample_messages, build_weekly_narrative


def grounding_check(tickets: pd.DataFrame, week_start: pd.Timestamp) -> dict:
    """Runs one real digest call for `week_start` and checks every cited
    ticket_id against the actual sample given to the model.
    """
    sampled = _sample_messages(tickets, week_start)
    sampled_ids_by_category = {cat: {tid for tid, _ in msgs} for cat, msgs in sampled.items()}

    narrative = build_weekly_narrative(tickets, week_start)
    if not narrative.get("available"):
        return {"week": week_start, "available": False, "reason": narrative.get("reason")}

    # Two very different failure modes get lumped together if we only check
    # "is this ticket_id in the category it was cited under": (a) the model
    # invents a ticket_id that doesn't exist anywhere -- a true
    # hallucination -- vs (b) the model cites a REAL ticket it was actually
    # given, sampled under a *different* category that week, because every
    # category's sample sits in the same prompt and the ticket is
    # topically relevant to the theme it's filed under. (b) is a labelling
    # slip, not a fabrication -- so it's tracked separately.
    all_sampled_ids_this_week = set().union(*sampled_ids_by_category.values()) if sampled_ids_by_category else set()
    all_real_ticket_ids = set(tickets["ticket_id"])

    total_themes = 0
    total_citations = 0
    bad_citations = []  # (category, theme, ticket_id, why)
    invented_categories = []

    for entry in narrative["categories"]:
        category = entry.get("category")
        if category not in sampled_ids_by_category:
            invented_categories.append(category)
            continue
        valid_ids = sampled_ids_by_category[category]
        for theme in entry.get("themes", []):
            total_themes += 1
            for tid in theme.get("ticket_ids", []):
                total_citations += 1
                if tid not in valid_ids:
                    if tid in all_sampled_ids_this_week:
                        why = "cross_category: real ticket, sampled under a different category this week"
                    elif tid in all_real_ticket_ids:
                        why = "unsampled_but_real: real ticket, but not given to the model at all this call"
                    else:
                        why = "fabricated: ticket_id does not exist in the dataset"
                    bad_citations.append((category, theme.get("theme"), tid, why))
            if not theme.get("ticket_ids"):
                bad_citations.append((category, theme.get("theme"), None, "no citations at all"))

    return {
        "week": week_start,
        "available": True,
        "total_themes": total_themes,
        "total_citations": total_citations,
        "bad_citations": bad_citations,
        "fabricated_citations": sum(1 for bc in bad_citations if bc[3].startswith("fabricated")),
        "invented_categories": invented_categories,
        "citation_validity_rate": (
            1.0 if total_citations == 0 else 1 - len(bad_citations) / total_citations
        ),
    }


def run_grounding_eval(tickets: pd.DataFrame, n_weeks: int = 15, seed: int = 42) -> pd.DataFrame:
    weeks = sorted(tickets["week_start"].unique())
    rng = random.Random(seed)
    sample_weeks = rng.sample(weeks, min(n_weeks, len(weeks)))

    rows = []
    for week in sample_weeks:
        result = grounding_check(tickets, pd.Timestamp(week))
        rows.append(
            {
                "week": week,
                "available": result["available"],
                "total_themes": result.get("total_themes"),
                "total_citations": result.get("total_citations"),
                "bad_citations": len(result.get("bad_citations", [])),
                "fabricated_citations": result.get("fabricated_citations", 0),
                "invented_categories": len(result.get("invented_categories", [])),
                "citation_validity_rate": result.get("citation_validity_rate"),
            }
        )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    from dotenv import load_dotenv

    from src.data import load_tickets

    load_dotenv()
    tickets = load_tickets()
    results = run_grounding_eval(tickets, n_weeks=15)
    print(results.to_string())

    available = results[results["available"]]
    print(f"\nweeks checked: {len(results)} (available: {len(available)})")
    print(f"citation validity rate (mean over weeks): {available['citation_validity_rate'].mean():.4f}")
    print(f"total themes: {available['total_themes'].sum()}")
    print(f"total citations: {available['total_citations'].sum()}")
    print(f"total bad citations (any mismatch): {available['bad_citations'].sum()}")
    print(f"  of which truly fabricated (ticket_id doesn't exist): {available['fabricated_citations'].sum()}")
    print(f"  the rest are cross-category: real ticket, wrong category header")
    print(f"weeks with invented categories: {(available['invented_categories'] > 0).sum()}")

    results.to_csv("eval_grounding_results.csv", index=False)
    print("\nSaved to eval_grounding_results.csv")
