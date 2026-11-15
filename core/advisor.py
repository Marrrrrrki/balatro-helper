
from __future__ import annotations

from itertools import combinations
import random

from .evaluator import best_play, evaluate
from .scoring import score_hand


def _nonnegative_int(value):
    """Return a safe non-negative integer, or None when unknown."""
    if value is None or value == "?":
        return None

    try:
        return max(0, int(value))
    except (TypeError, ValueError, OverflowError):
        return None


def analyze(state, simulations=120):
    """Compare the best current play with sampled discard outcomes.

    Discard estimates are heuristic. Each candidate is sampled from the
    supplied remaining deck, then the best 1-5 card play is scored.
    """
    hand = state.get("hand") or []
    levels = state.get("hand_levels") or {}
    jokers = state.get("jokers") or []
    deck = state.get("deck") or []

    def scorer(chosen, evaluation, hand_levels):
        held = [card for card in hand if card not in chosen]
        return score_hand(
            chosen, evaluation, hand_levels, jokers, held
        )

    current = best_play(hand, levels, scorer) if hand else None

    if not hand:
        return {
            "best": None,
            "discard": None,
            "recommendation": "WAIT",
            "reason": "No cards are available in the current hand.",
        }

    discards_left = _nonnegative_int(state.get("discards_left"))

    if not deck:
        return {
            "best": current,
            "discard": None,
            "recommendation": "PLAY",
            "reason": "No drawable cards remain for a replacement hand.",
        }

    if discards_left == 0:
        return {
            "best": current,
            "discard": None,
            "recommendation": "PLAY",
            "reason": "No discards remain, so play the best current hand.",
        }

    # Do not guess when the save does not provide a usable discard count.
    if discards_left is None:
        return {
            "best": current,
            "discard": None,
            "recommendation": "PLAY",
            "reason": (
                "The remaining discard count is unknown; "
                "keeping the current hand is the safe recommendation."
            ),
        }

    try:
        simulation_count = max(1, min(5000, int(simulations)))
    except (TypeError, ValueError, OverflowError):
        simulation_count = 120

    max_discard = min(5, len(hand), discards_left)

    if max_discard <= 0:
        return {
            "best": current,
            "discard": None,
            "recommendation": "PLAY",
            "reason": "There are no legal discards available.",
        }

    rng = random.Random(24017)
    candidates = []

    for count in range(1, max_discard + 1):
        for indices in combinations(range(len(hand)), count):
            keep = [
                card
                for i, card in enumerate(hand)
                if i not in indices
            ]

            total_score = 0

            for _ in range(simulation_count):
                draw_count = min(count, len(deck))
                draw = rng.sample(deck, draw_count)
                simulated_hand = keep + draw

                best_simulated_score = 0

                for size in range(
                    1, min(5, len(simulated_hand)) + 1
                ):
                    for chosen in combinations(simulated_hand, size):
                        chosen_list = list(chosen)
                        evaluation = evaluate(chosen_list)

                        held = [
                            card
                            for card in simulated_hand
                            if card not in chosen
                        ]

                        result = score_hand(
                            chosen_list,
                            evaluation,
                            levels,
                            jokers,
                            held,
                        )

                        best_simulated_score = max(
                            best_simulated_score,
                            result["score"],
                        )

                total_score += best_simulated_score

            candidates.append({
                "indices": indices,
                "cards": [hand[i] for i in indices],
                "ev": total_score / simulation_count,
                "simulations": simulation_count,
            })

    discard = max(
        candidates,
        key=lambda candidate: candidate["ev"],
        default=None,
    )

    play_score = current["score"] if current else 0

    if discard and discard["ev"] > play_score * 1.15:
        recommendation = "DISCARD"
        reason = (
            f"Estimated replacement-hand score "
            f"({discard['ev']:,.0f}) is more than 15% above "
            f"the best current play ({play_score:,.0f}). "
            f"This estimate uses {simulation_count:,} simulations."
        )
    else:
        recommendation = "PLAY"

        if discard:
            reason = (
                f"The best current play ({play_score:,.0f}) is at "
                f"least as attractive as the estimated discard "
                f"outcome ({discard['ev']:,.0f})."
            )
        else:
            reason = "No legal discard candidates could be evaluated."

    return {
        "best": current,
        "discard": discard,
        "recommendation": recommendation,
        "reason": reason,
    }
