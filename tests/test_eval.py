import sys
from pathlib import Path
from unittest.mock import patch

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import eval as eval_mod  # noqa: E402


FAKE_SAMPLE = {
    "Billing & Payments": [("TK-1", "billed twice"), ("TK-2", "gst invoice please")],
    "Connectivity": [("TK-3", "keeps disconnecting")],
}
# TK-4 exists in the dataset but wasn't given to the model this call (not in
# FAKE_SAMPLE) -- distinct from TK-999, which doesn't exist at all.
FAKE_TICKETS = pd.DataFrame({"ticket_id": ["TK-1", "TK-2", "TK-3", "TK-4"]})


def test_grounding_check_flags_fabricated_ticket_id():
    fake_narrative = {
        "available": True,
        "categories": [
            {
                "category": "Billing & Payments",
                "themes": [{"theme": "double charge", "ticket_ids": ["TK-1", "TK-999"]}],
            }
        ],
    }
    with patch.object(eval_mod, "_sample_messages", return_value=FAKE_SAMPLE), patch.object(
        eval_mod, "build_weekly_narrative", return_value=fake_narrative
    ):
        result = eval_mod.grounding_check(FAKE_TICKETS, pd.Timestamp("2025-01-06"))

    assert result["total_citations"] == 2
    assert len(result["bad_citations"]) == 1
    assert result["bad_citations"][0][2] == "TK-999"
    assert result["bad_citations"][0][3].startswith("fabricated")
    assert result["fabricated_citations"] == 1
    assert result["citation_validity_rate"] == 0.5


def test_grounding_check_distinguishes_cross_category_from_fabrication():
    # TK-3 is real and was given to the model this call, just under
    # Connectivity, not Billing & Payments -- a labelling slip, not a
    # fabrication, and should be classified as such.
    fake_narrative = {
        "available": True,
        "categories": [
            {
                "category": "Billing & Payments",
                "themes": [{"theme": "misfiled complaint", "ticket_ids": ["TK-3"]}],
            }
        ],
    }
    with patch.object(eval_mod, "_sample_messages", return_value=FAKE_SAMPLE), patch.object(
        eval_mod, "build_weekly_narrative", return_value=fake_narrative
    ):
        result = eval_mod.grounding_check(FAKE_TICKETS, pd.Timestamp("2025-01-06"))

    assert len(result["bad_citations"]) == 1
    assert result["bad_citations"][0][3].startswith("cross_category")
    assert result["fabricated_citations"] == 0


def test_grounding_check_flags_unsampled_but_real_ticket_id():
    # TK-4 is a real ticket_id in the dataset but wasn't sampled/given to
    # the model at all this call -- different failure mode again.
    fake_narrative = {
        "available": True,
        "categories": [
            {
                "category": "Billing & Payments",
                "themes": [{"theme": "double charge", "ticket_ids": ["TK-4"]}],
            }
        ],
    }
    with patch.object(eval_mod, "_sample_messages", return_value=FAKE_SAMPLE), patch.object(
        eval_mod, "build_weekly_narrative", return_value=fake_narrative
    ):
        result = eval_mod.grounding_check(FAKE_TICKETS, pd.Timestamp("2025-01-06"))

    assert result["bad_citations"][0][3].startswith("unsampled_but_real")
    assert result["fabricated_citations"] == 0


def test_grounding_check_flags_invented_category():
    fake_narrative = {
        "available": True,
        "categories": [{"category": "Made Up Category", "themes": [{"theme": "x", "ticket_ids": []}]}],
    }
    with patch.object(eval_mod, "_sample_messages", return_value=FAKE_SAMPLE), patch.object(
        eval_mod, "build_weekly_narrative", return_value=fake_narrative
    ):
        result = eval_mod.grounding_check(FAKE_TICKETS, pd.Timestamp("2025-01-06"))

    assert result["invented_categories"] == ["Made Up Category"]


def test_grounding_check_perfect_score_when_all_valid():
    fake_narrative = {
        "available": True,
        "categories": [
            {
                "category": "Connectivity",
                "themes": [{"theme": "drops connection", "ticket_ids": ["TK-3"]}],
            }
        ],
    }
    with patch.object(eval_mod, "_sample_messages", return_value=FAKE_SAMPLE), patch.object(
        eval_mod, "build_weekly_narrative", return_value=fake_narrative
    ):
        result = eval_mod.grounding_check(FAKE_TICKETS, pd.Timestamp("2025-01-06"))

    assert result["citation_validity_rate"] == 1.0
    assert result["bad_citations"] == []


if __name__ == "__main__":
    test_grounding_check_flags_fabricated_ticket_id()
    test_grounding_check_distinguishes_cross_category_from_fabrication()
    test_grounding_check_flags_unsampled_but_real_ticket_id()
    test_grounding_check_flags_invented_category()
    test_grounding_check_perfect_score_when_all_valid()
    print("all tests passed")
