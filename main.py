"""CLI entrypoint: weekly digest + agent leaderboard for Vireo Audio support tickets.

Usage:
    python main.py digest [--week YYYY-MM-DD]
    python main.py leaderboard [--week YYYY-MM-DD]
    python main.py weeks              # list available week_start dates

With no --week, both commands use the most recent complete week in the data.
"""
from __future__ import annotations

import argparse
import sys

import pandas as pd
from dotenv import load_dotenv

from src.data import load_tickets
from src.digest import build_weekly_narrative, build_weekly_stats
from src.leaderboard import excluded_team_summary, weekly_leaderboard

load_dotenv()


def _latest_complete_week(tickets: pd.DataFrame) -> pd.Timestamp:
    weeks = sorted(tickets["week_start"].unique())
    return pd.Timestamp(weeks[-2] if len(weeks) > 1 else weeks[-1])


def cmd_digest(tickets: pd.DataFrame, week: pd.Timestamp) -> None:
    print(f"\n=== Weekly complaint digest: {week.date()} to {(week + pd.Timedelta(days=6)).date()} ===\n")

    stats = build_weekly_stats(tickets, week)
    print(f"{'Category':<24} {'Tickets':>8} {'vs prior wk':>12} {'Repeat %':>9} {'Avg CSAT':>9}")
    for category, row in stats.iterrows():
        print(
            f"{category:<24} {int(row['tickets']):>8} {int(row['wow_change']):>+12} "
            f"{row['repeat_contact_rate']*100:>8.1f}% {row['avg_csat']:>9.2f}"
        )

    week_ticket_count = int(stats["tickets"].sum())
    week_repeat_rate = tickets[tickets["week_start"] == week]["is_repeat_contact"].mean()
    print(f"\nRepeat-contact rate this week: {week_repeat_rate*100:.1f}% ({week_ticket_count} tickets)")

    print("\n--- Themes (LLM, grounded to sampled messages) ---")
    narrative = build_weekly_narrative(tickets, week)
    if not narrative["available"]:
        print(f"[unavailable: {narrative['reason']}]")
        return
    for entry in narrative["categories"]:
        print(f"\n{entry['category']}:")
        for theme in entry["themes"]:
            ids = ", ".join(theme["ticket_ids"])
            print(f"  - {theme['theme']} ({ids})")


def cmd_leaderboard(tickets: pd.DataFrame, week: pd.Timestamp) -> None:
    print(f"\n=== Agent leaderboard: {week.date()} to {(week + pd.Timedelta(days=6)).date()} ===\n")
    board = weekly_leaderboard(tickets, week)
    print(board.to_string())

    excluded = excluded_team_summary(tickets, week)
    if len(excluded):
        print("\n--- Escalations & Warranty (reported, not ranked -- see README) ---")
        print(excluded.to_string(index=False))


def cmd_weeks(tickets: pd.DataFrame) -> None:
    for week in sorted(tickets["week_start"].unique()):
        print(pd.Timestamp(week).date())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ("digest", "leaderboard"):
        p = sub.add_parser(name)
        p.add_argument("--week", type=str, default=None, help="Monday of the target week, YYYY-MM-DD")

    sub.add_parser("weeks")

    args = parser.parse_args()
    tickets = load_tickets()

    if args.command == "weeks":
        cmd_weeks(tickets)
        return

    week = pd.Timestamp(args.week) if args.week else _latest_complete_week(tickets)
    week = week - pd.to_timedelta(week.weekday(), unit="D")  # snap to Monday

    if args.command == "digest":
        cmd_digest(tickets, week)
    elif args.command == "leaderboard":
        cmd_leaderboard(tickets, week)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
