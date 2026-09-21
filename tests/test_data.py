import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data import load_agents, load_tickets  # noqa: E402


def test_load_tickets_shape_and_columns():
    agents = load_agents()
    tickets = load_tickets(agents=agents)
    assert len(tickets) == 12528
    for col in ["agent_name", "agent_team", "week_start", "is_repeat_contact", "resolution_time_valid"]:
        assert col in tickets.columns


def test_negative_resolution_all_legacy():
    tickets = load_tickets()
    invalid = tickets[~tickets["resolution_time_valid"]]
    assert len(invalid) > 0
    assert (invalid["source_system"] == "legacy_fd").all()


def test_repeat_contact_rate_in_expected_range():
    tickets = load_tickets()
    rate = tickets["is_repeat_contact"].mean()
    assert 0.05 < rate < 0.12


def test_every_agent_id_resolves_to_roster():
    tickets = load_tickets()
    assert tickets["agent_name"].isna().sum() == 0


if __name__ == "__main__":
    test_load_tickets_shape_and_columns()
    test_negative_resolution_all_legacy()
    test_repeat_contact_rate_in_expected_range()
    test_every_agent_id_resolves_to_roster()
    print("all tests passed")
