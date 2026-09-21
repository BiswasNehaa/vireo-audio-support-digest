import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data import load_tickets  # noqa: E402
from src.digest import build_weekly_narrative, build_weekly_stats  # noqa: E402


def _busiest_week(tickets):
    weeks = tickets["week_start"]
    return weeks.value_counts().idxmax()


def test_weekly_stats_columns_and_wow():
    tickets = load_tickets()
    week = _busiest_week(tickets)
    stats = build_weekly_stats(tickets, week)
    for col in ["tickets", "tickets_prior_week", "avg_csat", "repeat_contact_rate", "wow_change"]:
        assert col in stats.columns
    assert stats["tickets"].sum() > 0
    assert stats["wow_change"].equals(stats["tickets"] - stats["tickets_prior_week"])


def test_narrative_degrades_gracefully_without_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    tickets = load_tickets()
    week = _busiest_week(tickets)
    result = build_weekly_narrative(tickets, week)
    assert result["available"] is False
    assert "reason" in result
    assert result["categories"] == []


if __name__ == "__main__":
    test_weekly_stats_columns_and_wow()

    class _MP:
        def delenv(self, name, raising=False):
            import os

            os.environ.pop(name, None)

    test_narrative_degrades_gracefully_without_api_key(_MP())
    print("all tests passed")
