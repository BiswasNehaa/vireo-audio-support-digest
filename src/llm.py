"""Thin Anthropic wrapper for the digest's theme-summarisation step.

Deliberately the only place in the codebase that calls out to a model.
Everything that can be computed with pandas (counts, rates, the
leaderboard, the business-KPI number) is computed with pandas -- the LLM
is used for exactly one thing it's actually needed for: turning a batch of
free-text customer messages into short, human-readable complaint themes.

Cost shape matters here (see memo): one call per week covering ALL
categories, not one call per ticket or per category, and not one call per
week * category. A week's digest is capped at MAX_MESSAGES_PER_WEEK
sampled messages regardless of how many tickets that week actually has, so
the bill doesn't scale with ticket volume past that cap.
"""
from __future__ import annotations

import json
import os

MODEL = "claude-haiku-4-5-20251001"
MAX_MESSAGES_PER_CATEGORY = 8
MAX_MESSAGES_PER_WEEK = 60

SYSTEM_PROMPT = """You are summarising a week of customer-support tickets for a consumer \
electronics brand's support-operations lead. You will be given customer messages grouped \
by category, each tagged with its ticket_id. For each category, identify at most 3 distinct \
complaint sub-themes actually present in the given messages (e.g. within "Connectivity": \
"earbuds drop connection mid-call" vs "won't pair with Android after update" are different \
themes -- don't just restate the category name as the theme).

Rules:
- Only describe themes you can point to in the given messages. Never invent a theme, a \
count, or a ticket_id that isn't in the input.
- For each theme, cite the ticket_ids (from the input) that support it.
- If a category's messages don't show a clear sub-theme beyond the category itself, say so \
plainly rather than inventing one.
- Keep each theme description to one plain-English sentence, no jargon.

Respond with JSON only, matching this shape:
{"categories": [{"category": str, "themes": [{"theme": str, "ticket_ids": [str, ...]}]}]}
"""


class LLMUnavailable(RuntimeError):
    pass


def get_client():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise LLMUnavailable(
            "ANTHROPIC_API_KEY is not set. Digest will run with deterministic "
            "category/volume stats only -- no theme narrative. See README.md."
        )
    import anthropic

    return anthropic.Anthropic(api_key=api_key)


def summarise_week(category_messages: dict[str, list[tuple[str, str]]]) -> dict:
    """category_messages: {category: [(ticket_id, message), ...]}, already
    sampled/capped by the caller. Returns the parsed JSON described above.
    Raises LLMUnavailable if no API key is configured.
    """
    client = get_client()

    lines = []
    for category, messages in category_messages.items():
        lines.append(f"## {category} ({len(messages)} sample messages)")
        for ticket_id, message in messages:
            snippet = " ".join(message.split())[:300]
            lines.append(f"- [{ticket_id}] {snippet}")
    user_content = "\n".join(lines)

    response = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )
    text = response.content[0].text
    return json.loads(text)
