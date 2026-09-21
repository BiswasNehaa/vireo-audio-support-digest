import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data import load_tickets  # noqa: E402
from src.metrics import (  # noqa: E402
    cost_of_repeat_contacts,
    repeat_contact_summary,
    weekly_repeat_contact_rate,
)


def test_repeat_contact_summary():
    tickets = load_tickets()
    s = repeat_contact_summary(tickets)
    assert s["total_tickets"] == 12528
    assert 0.05 < s["repeat_contact_rate"] < 0.12
    assert s["repeat_contacts"] == round(s["repeat_contact_rate"] * s["total_tickets"])


def test_weekly_rate_shape():
    tickets = load_tickets()
    w = weekly_repeat_contact_rate(tickets)
    assert w["rate"].between(0, 1).all()
    assert len(w) > 50  # ~78 weeks in an 18-month pack


def test_cost_of_repeat_contacts_positive_and_scales():
    tickets = load_tickets()
    current = repeat_contact_summary(tickets)["repeat_contact_rate"]
    result = cost_of_repeat_contacts(tickets, target_rate=current - 0.03)
    assert result["value_per_quarter_inr"] > 0
    assert result["value_per_year_inr"] == result["value_per_week_inr"] * 52


def test_cost_rejects_target_above_current():
    tickets = load_tickets()
    current = repeat_contact_summary(tickets)["repeat_contact_rate"]
    try:
        cost_of_repeat_contacts(tickets, target_rate=current + 0.01)
        assert False, "expected ValueError"
    except ValueError:
        pass


if __name__ == "__main__":
    test_repeat_contact_summary()
    test_weekly_rate_shape()
    test_cost_of_repeat_contacts_positive_and_scales()
    test_cost_rejects_target_above_current()
    print("all tests passed")
