"""Agent leaderboard: tickets closed per week.

"Closed" = status in {resolved, closed} (both always carry a resolved_at;
open/pending never do), counted in the week the agent closed it, not the
week it was opened.

Neha Kulkarni (Support Ops Manager) asked, in the email thread, not to
rank Escalations & Warranty on ticket counts -- their cases run days by
design, so a raw-count leaderboard makes them look idle when they aren't.
We honour that: the warranty team is reported separately, never mixed
into the ranked table.
"""
from __future__ import annotations

import pandas as pd

EXCLUDE_FROM_RANKING = {"Escalations & Warranty"}


def _closed(tickets: pd.DataFrame) -> pd.DataFrame:
    return tickets[tickets["status"].isin(["resolved", "closed"])].copy()


def weekly_leaderboard(tickets: pd.DataFrame, week_start: pd.Timestamp) -> pd.DataFrame:
    """Ranked tickets-closed-per-agent table for one week, ranked agents only."""
    closed = _closed(tickets)
    closed = closed[closed["resolved_at"].dt.normalize() >= week_start]
    closed = closed[closed["resolved_at"].dt.normalize() < week_start + pd.Timedelta(days=7)]
    closed = closed[~closed["agent_team"].isin(EXCLUDE_FROM_RANKING)]

    board = (
        closed.groupby(["agent_id", "agent_name", "agent_team", "site"])
        .size()
        .reset_index(name="tickets_closed")
        .sort_values("tickets_closed", ascending=False)
        .reset_index(drop=True)
    )
    board.index = board.index + 1
    board.index.name = "rank"
    return board


def excluded_team_summary(tickets: pd.DataFrame, week_start: pd.Timestamp) -> pd.DataFrame:
    """Same-shape table for the excluded team(s), reported but not ranked."""
    closed = _closed(tickets)
    closed = closed[closed["resolved_at"].dt.normalize() >= week_start]
    closed = closed[closed["resolved_at"].dt.normalize() < week_start + pd.Timedelta(days=7)]
    closed = closed[closed["agent_team"].isin(EXCLUDE_FROM_RANKING)]

    return (
        closed.groupby(["agent_id", "agent_name", "agent_team"])
        .agg(tickets_closed=("ticket_id", "size"), median_resolution_hours=("resolution_hours", "median"))
        .reset_index()
        .sort_values("tickets_closed", ascending=False)
    )
