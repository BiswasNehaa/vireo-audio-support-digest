"""Load and clean Vireo Audio support-ticket data.

Two data-quality issues discovered while exploring the pack, both handled
here rather than left for every downstream script to rediscover:

1. Legacy tickets (source_system == "legacy_fd", migrated from Freshdesk
   before 14 Sep 2025) sometimes have resolved_at earlier than created_at --
   the resolution time was reconstructed from an event log, not recorded
   live, and ~60% of that subset comes out negative. We keep the rows (never
   silently drop data) but mark them with resolution_time_valid=False so
   metrics can choose to exclude them.
2. tickets.assigned_team is where the ticket was FIRST routed, which is not
   always the resolving agent's actual team (12% mismatch) -- e.g. a chat
   ticket transferred to Billing and closed by a Billing agent still shows
   assigned_team="Chat Frontline". The agent's real team, joined from
   agents.csv, is what the leaderboard groups by, not assigned_team.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_agents(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    agents = pd.read_csv(data_dir / "agents.csv")
    agents["from_date"] = pd.to_datetime(agents["from_date"])
    agents["to_date"] = pd.to_datetime(agents["to_date"])
    return agents


def load_tickets(data_dir: Path = DATA_DIR, agents: pd.DataFrame | None = None) -> pd.DataFrame:
    tickets = pd.read_csv(data_dir / "tickets.csv")
    tickets["created_at"] = pd.to_datetime(tickets["created_at"])
    tickets["first_response_at"] = pd.to_datetime(tickets["first_response_at"], errors="coerce")
    tickets["resolved_at"] = pd.to_datetime(tickets["resolved_at"], errors="coerce")

    tickets["resolution_hours"] = (
        tickets["resolved_at"] - tickets["created_at"]
    ).dt.total_seconds() / 3600
    tickets["response_hours"] = (
        tickets["first_response_at"] - tickets["created_at"]
    ).dt.total_seconds() / 3600
    tickets["resolution_time_valid"] = tickets["resolution_hours"].isna() | (
        tickets["resolution_hours"] >= 0
    )

    if agents is None:
        agents = load_agents(data_dir)
    roster = agents[["agent_id", "name", "site", "team", "tier"]].rename(
        columns={"name": "agent_name", "team": "agent_team"}
    )
    tickets = tickets.merge(roster, on="agent_id", how="left")

    tickets["week_start"] = (
        tickets["created_at"] - pd.to_timedelta(tickets["created_at"].dt.weekday, unit="D")
    ).dt.normalize()

    tickets = add_repeat_contact_flag(tickets)
    return tickets


def add_repeat_contact_flag(tickets: pd.DataFrame, window_days: int = 7) -> pd.DataFrame:
    """Flag a ticket as a repeat contact: same customer, same category,
    opened within `window_days` of that customer's previous ticket in the
    same category. This is a proxy for "customer had to contact us again
    about the same thing" -- there's no ground-truth linking field in the
    export, so it's inferred from timing + category rather than measured
    directly.
    """
    t = tickets.sort_values(["customer_id", "created_at"]).copy()
    prev_created = t.groupby("customer_id")["created_at"].shift(1)
    prev_category = t.groupby("customer_id")["category"].shift(1)
    gap_days = (t["created_at"] - prev_created).dt.total_seconds() / 86400
    t["is_repeat_contact"] = (gap_days <= window_days) & (t["category"] == prev_category)
    return t.sort_index()


def load_customers(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    customers = pd.read_csv(data_dir / "customers.csv")
    customers["signup_date"] = pd.to_datetime(customers["signup_date"])
    return customers


def load_orders(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    return pd.read_csv(data_dir / "orders.csv")


def load_products(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    products = pd.read_csv(data_dir / "products.csv")
    products["launch_date"] = pd.to_datetime(products["launch_date"])
    return products
