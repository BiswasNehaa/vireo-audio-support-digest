"""Business-KPI computation: the repeat-contact rate and its cost.

Business goal picked from the data (see memo/ for the write-up): Vireo's
own emails flag a hunch -- "customers who open with 'I already told your
colleague this'" -- and flag a cost/contact figure (Rs 290 blended,
per Priya's email) to value it against. This module measures that rate
from the ticket data and prices a reduction in it.

Repeat contact := same customer, same category, opened within 7 days of
that customer's previous ticket in the same category (src/data.py). There
is no ground-truth "this is a repeat" field in the export, so this is a
proxy, not a measured fact -- see memo for the false-positive/negative
discussion.
"""
from __future__ import annotations

import pandas as pd

COST_PER_CONTACT_INR = 290  # blended, per Priya Raman's email (09 Sep 2026)
REAL_WEEKLY_VOLUME = 650  # Vireo's actual ticket volume, per the brief -- our
# data pack averages ~160 tickets/week (12,528 tickets / 78 weeks), so it is
# a partial sample. Rates are measured on the sample and then applied to
# Vireo's real volume to price the impact -- see memo for this assumption.


def repeat_contact_summary(tickets: pd.DataFrame) -> dict:
    total = len(tickets)
    repeats = int(tickets["is_repeat_contact"].sum())
    rate = repeats / total
    return {
        "total_tickets": total,
        "repeat_contacts": repeats,
        "repeat_contact_rate": rate,
        "sample_weeks": tickets["week_start"].nunique(),
        "sample_avg_weekly_volume": total / tickets["week_start"].nunique(),
    }


def weekly_repeat_contact_rate(tickets: pd.DataFrame) -> pd.DataFrame:
    g = tickets.groupby("week_start")["is_repeat_contact"].agg(["sum", "count"])
    g["rate"] = g["sum"] / g["count"]
    return g.rename(columns={"sum": "repeat_contacts", "count": "total_tickets"})


def cost_of_repeat_contacts(
    tickets: pd.DataFrame,
    target_rate: float,
    real_weekly_volume: int = REAL_WEEKLY_VOLUME,
    cost_per_contact_inr: float = COST_PER_CONTACT_INR,
) -> dict:
    """Price the gap between the measured repeat-contact rate and a target
    rate, scaled to Vireo's real weekly volume (the sample under-covers it).
    """
    current_rate = repeat_contact_summary(tickets)["repeat_contact_rate"]
    if target_rate >= current_rate:
        raise ValueError("target_rate must be below the measured current_rate")

    contacts_avoided_per_week = real_weekly_volume * (current_rate - target_rate)
    value_per_week_inr = contacts_avoided_per_week * cost_per_contact_inr
    return {
        "current_rate": current_rate,
        "target_rate": target_rate,
        "real_weekly_volume": real_weekly_volume,
        "contacts_avoided_per_week": contacts_avoided_per_week,
        "value_per_week_inr": value_per_week_inr,
        "value_per_quarter_inr": value_per_week_inr * 13,
        "value_per_year_inr": value_per_week_inr * 52,
    }
