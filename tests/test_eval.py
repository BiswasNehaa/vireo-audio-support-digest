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


def test_grounding_check_flags_hallucinated_ticket_id():
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
        result = eval_mod.grounding_check(pd.DataFrame(), pd.Timestamp("2025-01-06"))

    assert result["total_citations"] == 2
    assert len(result["bad_citations"]) == 1
    assert result["bad_citations"][0][2] == "TK-999"
    assert result["citation_validity_rate"] == 0.5


def test_grounding_check_flags_invented_category():
    fake_narrative = {
        "available": True,
        "categories": [{"category": "Made Up Category", "themes": [{"theme": "x", "ticket_ids": []}]}],
    }
    with patch.object(eval_mod, "_sample_messages", return_value=FAKE_SAMPLE), patch.object(
        eval_mod, "build_weekly_narrative", return_value=fake_narrative
    ):
        result = eval_mod.grounding_check(pd.DataFrame(), pd.Timestamp("2025-01-06"))

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
        result = eval_mod.grounding_check(pd.DataFrame(), pd.Timestamp("2025-01-06"))

    assert result["citation_validity_rate"] == 1.0
    assert result["bad_citations"] == []


if __name__ == "__main__":
    test_grounding_check_flags_hallucinated_ticket_id()
    test_grounding_check_flags_invented_category()
    test_grounding_check_perfect_score_when_all_valid()
    print("all tests passed")
