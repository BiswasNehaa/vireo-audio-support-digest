"""Weekly complaint digest: deterministic stats + an optional LLM theme layer.

build_weekly_stats() always works (pure pandas). build_weekly_narrative()
additionally calls the LLM to turn sampled free text into short themes, and
degrades to "no narrative, see stats" if no API key is configured -- the
tool is still useful without one, just less readable.
"""
from __future__ import annotations

import pandas as pd

from src.llm import MAX_MESSAGES_PER_CATEGORY, MAX_MESSAGES_PER_WEEK, LLMUnavailable, summarise_week


def _week_slice(tickets: pd.DataFrame, week_start: pd.Timestamp) -> pd.DataFrame:
    return tickets[
        (tickets["week_start"] == pd.Timestamp(week_start).normalize())
    ]


def build_weekly_stats(tickets: pd.DataFrame, week_start: pd.Timestamp) -> pd.DataFrame:
    """Per-category volume this week vs the prior week, CSAT, repeat-contact rate."""
    week_start = pd.Timestamp(week_start).normalize()
    prev_week_start = week_start - pd.Timedelta(days=7)

    this_week = _week_slice(tickets, week_start)
    prev_week = _week_slice(tickets, prev_week_start)

    this_counts = this_week.groupby("category").size().rename("tickets")
    prev_counts = prev_week.groupby("category").size().rename("tickets_prior_week")
    csat = this_week.groupby("category")["csat_score"].apply(
        lambda s: s[s > 0].mean()
    ).rename("avg_csat")
    repeat_rate = this_week.groupby("category")["is_repeat_contact"].mean().rename(
        "repeat_contact_rate"
    )

    stats = pd.concat([this_counts, prev_counts, csat, repeat_rate], axis=1).fillna(
        {"tickets": 0, "tickets_prior_week": 0}
    )
    stats["wow_change"] = stats["tickets"] - stats["tickets_prior_week"]
    return stats.sort_values("tickets", ascending=False)


def _sample_messages(tickets: pd.DataFrame, week_start: pd.Timestamp, seed: int = 0) -> dict:
    week = _week_slice(tickets, week_start)
    stats = build_weekly_stats(tickets, week_start)
    # Spend the per-week message budget on the biggest categories first.
    budget = MAX_MESSAGES_PER_WEEK
    sampled = {}
    for category in stats.index:
        if budget <= 0:
            break
        cat_tickets = week[week["category"] == category]
        n = min(MAX_MESSAGES_PER_CATEGORY, budget, len(cat_tickets))
        chosen = cat_tickets.sample(n=n, random_state=seed)
        sampled[category] = list(zip(chosen["ticket_id"], chosen["customer_message"].fillna("")))
        budget -= n
    return sampled


def build_weekly_narrative(tickets: pd.DataFrame, week_start: pd.Timestamp) -> dict:
    """Returns {"available": bool, "categories": [...] } -- available=False
    (with a reason) when there's no API key, rather than raising, so callers
    can render "stats only" instead of crashing the whole digest.
    """
    try:
        sampled = _sample_messages(tickets, week_start)
        result = summarise_week(sampled)
        result["available"] = True
        return result
    except LLMUnavailable as e:
        return {"available": False, "reason": str(e), "categories": []}
