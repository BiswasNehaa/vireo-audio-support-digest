import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data import load_tickets  # noqa: E402
from src.leaderboard import excluded_team_summary, weekly_leaderboard  # noqa: E402


def _busiest_week(tickets):
    closed = tickets[tickets["status"].isin(["resolved", "closed"])]
    weeks = (
        closed["resolved_at"].dt.normalize()
        - pd.to_timedelta(closed["resolved_at"].dt.weekday, unit="D")
    )
    return weeks.value_counts().idxmax()


def test_leaderboard_excludes_warranty_team():
    tickets = load_tickets()
    week = _busiest_week(tickets)
    board = weekly_leaderboard(tickets, week)
    assert "Escalations & Warranty" not in board["agent_team"].values
    assert len(board) > 0
    assert board["tickets_closed"].is_monotonic_decreasing


def test_excluded_team_summary_only_has_warranty():
    tickets = load_tickets()
    week = _busiest_week(tickets)
    summary = excluded_team_summary(tickets, week)
    if len(summary):
        assert set(summary["agent_team"].unique()) == {"Escalations & Warranty"}


def test_leaderboard_counts_match_manual_filter():
    tickets = load_tickets()
    week = _busiest_week(tickets)
    board = weekly_leaderboard(tickets, week)
    total_ranked = board["tickets_closed"].sum()

    closed = tickets[tickets["status"].isin(["resolved", "closed"])]
    mask = (
        (closed["resolved_at"].dt.normalize() >= week)
        & (closed["resolved_at"].dt.normalize() < week + pd.Timedelta(days=7))
        & (closed["agent_team"] != "Escalations & Warranty")
    )
    assert total_ranked == mask.sum()


if __name__ == "__main__":
    test_leaderboard_excludes_warranty_team()
    test_excluded_team_summary_only_has_warranty()
    test_leaderboard_counts_match_manual_filter()
    print("all tests passed")
