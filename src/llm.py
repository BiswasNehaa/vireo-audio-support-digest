"""Thin LLM wrapper for the digest's theme-summarisation step.

Deliberately the only place in the codebase that calls out to a model.
Everything that can be computed with pandas (counts, rates, the
leaderboard, the business-KPI number) is computed with pandas -- the LLM
is used for exactly one thing it's actually needed for: turning a batch of
free-text customer messages into short, human-readable complaint themes.

Uses Groq's free-tier API (OpenAI-compatible) so a month of weekly digests
at Vireo's volume costs Rs 0 -- see memo for the arithmetic. Swappable to
any other OpenAI-compatible endpoint via LLM_BASE_URL/LLM_API_KEY/LLM_MODEL
if Groq's free tier ever isn't enough.

Cost shape matters here (see memo): one call per week covering ALL
categories, not one call per ticket or per category. A week's digest is
capped at MAX_MESSAGES_PER_WEEK sampled messages regardless of how many
tickets that week actually has, so the bill doesn't scale with ticket
volume past that cap.
"""
from __future__ import annotations

import json
import os

DEFAULT_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_MODEL = "openai/gpt-oss-120b"
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

Respond with JSON only, no markdown fences, matching this shape:
{"categories": [{"category": str, "themes": [{"theme": str, "ticket_ids": [str, ...]}]}]}
"""


class LLMUnavailable(RuntimeError):
    pass


def get_client():
    api_key = os.environ.get("LLM_API_KEY") or os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise LLMUnavailable(
            "No GROQ_API_KEY (or LLM_API_KEY) set. Digest will run with deterministic "
            "category/volume stats only -- no theme narrative. Free key: "
            "https://console.groq.com. See README.md."
        )
    from openai import OpenAI

    base_url = os.environ.get("LLM_BASE_URL", DEFAULT_BASE_URL)
    return OpenAI(api_key=api_key, base_url=base_url)


def _model() -> str:
    return os.environ.get("LLM_MODEL", DEFAULT_MODEL)


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
    return text.strip()


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
            snippet = " ".join(str(message).split())[:300]
            lines.append(f"- [{ticket_id}] {snippet}")
    user_content = "\n".join(lines)

    response = client.chat.completions.create(
        model=_model(),
        max_tokens=4000,
        temperature=0,
        # gpt-oss (the default Groq model) is a reasoning model: it spends
        # completion tokens on hidden reasoning before the JSON answer, and
        # at reasoning_effort="medium"/"high" that reasoning alone can eat
        # the whole max_tokens budget and cut the response off truncated
        # (finish_reason="length", empty .content). "low" leaves enough
        # headroom for this prompt's output.
        reasoning_effort="low",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    )
    text = response.choices[0].message.content
    return json.loads(_strip_code_fence(text))
