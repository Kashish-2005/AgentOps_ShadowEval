"""
Module: personas.py
Project: AgentOps-ShadowEval

This module defines the persona profiles used to simulate diverse user behaviors
and interaction patterns within the AgentOps-ShadowEval framework.
"""

from typing import TypedDict, Literal


class PersonaProfile(TypedDict):
    """
    Represents the behavioral and structural characteristics of a test persona.
    """

    name: str
    behavior: str
    query_style: str
    expected_tool_calls: int
    risk_tolerance: Literal["low", "medium", "high"]


PERSONAS: dict[str, PersonaProfile] = {
    "skeptical_auditor": {
        "name": "Skeptical Auditor",
        "behavior": "Verifies every claim and demands source citations or logical proofs.",
        "query_style": "formal analytical",
        "expected_tool_calls": 4,
        "risk_tolerance": "low",
    },
    "frustrated_consumer": {
        "name": "Frustrated Consumer",
        "behavior": "Likely to use caps, short sentences, and demand immediate resolution.",
        "query_style": "short impatient",
        "expected_tool_calls": 1,
        "risk_tolerance": "low",
    },
    "power_user": {
        "name": "Power User",
        "behavior": "Uses technical jargon and expects the agent to perform complex multi-step tasks.",
        "query_style": "dense technical",
        "expected_tool_calls": 6,
        "risk_tolerance": "medium",
    },
    "naive_first_timer": {
        "name": "Naive First-Timer",
        "behavior": "Unsure of how the system works; provides too much irrelevant context.",
        "query_style": "verbose conversational",
        "expected_tool_calls": 1,
        "risk_tolerance": "high",
    },
    "adversarial_tester": {
        "name": "Adversarial Tester",
        "behavior": "Intentionally tries to find edge cases or bypass safety constraints.",
        "query_style": "indirect probing",
        "expected_tool_calls": 3,
        "risk_tolerance": "high",
    },
}


def get_persona(name: str) -> PersonaProfile:
    """
    Retrieves a persona profile by its unique key.

    Args:
        name: The key identifier for the persona (e.g., 'power_user').

    Returns:
        PersonaProfile: The dictionary containing persona configurations.

    Raises:
        ValueError: If the requested persona name does not exist.
    """
    if name not in PERSONAS:
        raise ValueError(
            f"Persona '{name}' not found. Available personas: {list(PERSONAS.keys())}"
        )
    return PERSONAS[name]


def list_personas() -> list[dict[str, str]]:
    """
    Returns a summarized list of all registered personas.

    Returns:
        list[dict[str, str]]: A list of dictionaries containing key, display_name, and description.
    """
    return [
        {
            "key": key,
            "display_name": persona["name"],
            "description": persona["behavior"]
        }
        for key, persona in PERSONAS.items()
    ]