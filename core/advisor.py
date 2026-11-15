
from __future__ import annotations

from itertools import combinations
from functools import lru_cache
import random

from .evaluator import best_play, evaluate
from .scoring import score_hand
from .boss_blinds import get_blind_rules, apply_blind_to_levels


def _nonnegative_int(value):
    if value is None or value == "?":
        return None

    try:
        return max(0, int(value))
    except (TypeError, ValueError, OverflowError):
        return None


def _rank_number(value):
    if isinstance(value, dict):
        value = value.get("rank", value.get("id", value.get("value")))

    names = {
        "A": 14, "ACE": 14,
        "K": 13, "KING": 13,
        "Q": 12, "QUEEN": 12,
        "J": 11, "JACK": 11,
        "T": 10, "10": 10,
    }

    text = str(value).strip().upper()

    if text in names:
        return names[text]

    try:
        rank = int(text)
        return rank if 2 <= rank <= 14 else None
    except (TypeError, ValueError):
        return None


def analyze(state, simulations=120, objective="score"):
    """
    objective="score": maximise expected poker hand score.
    objective="money": prioritise Mail-In Rebate payouts.
    """

    hand = state.get("hand") or []
    original_levels = state.get("hand_levels") or {}
    jokers = state.get("jokers") or []
    deck = state.get("deck") or []

    objective = str(objective).lower()
    if objective not in ("score", "money"):
        objective = "score"

    blind_rules = get_blind_rules(state)
    levels = apply_blind_to_levels(original_levels, blind_rules)

    mail_joker_active = any(
        (joker.get("save_fields") or {}).get("center") == "j_mail"
        and not joker.get("debuff")
        for joker in jokers
    )

    mail_rank = _rank_number(state.get("mail_rank"))

    money_mode_active = (
        objective == "money"
        and mail_joker_active
        and mail_rank is not None
    )

    remaining_discards = _nonnegative_int(
        state.get("discards_left")
    )

    def scorer(chosen, evaluation, hand_levels):
        chosen_ids = {id(card) for card in chosen}
        held = [
            card for card in hand
            if id(card) not in chosen_ids
        ]

        return score_hand(
            chosen,
            evaluation,
            hand_levels,
            jokers,
            held,
            remaining_discards=remaining_discards,
            remaining_deck=len(deck),
            blind_rules=blind_rules,
        )

    current = best_play(
        hand,
        levels,
        scorer,
        blind_rules=blind_rules,
    ) if hand else None

    if not hand:
        return {
            "best": None,
            "discard": None,
            "recommendation": "WAIT",
            "reason": "No cards are available in the current hand.",
            "objective": objective,
            "blind_rules": blind_rules,
        }

    exact_cards = blind_rules.get("exact_cards")

    if exact_cards and len(hand) < exact_cards:
        return {
            "best": None,
            "discard": None,
            "recommendation": "WAIT",
            "reason": (
                f"{blind_rules['name']} requires exactly "
                f"{exact_cards} cards, but only {len(hand)} "
                "cards are currently available."
            ),
            "objective": objective,
            "blind_rules": blind_rules,
        }

    if current is None:
        return {
            "best": None,
            "discard": None,
            "recommendation": "WAIT",
            "reason": "No legal hand could be found under this blind's rules.",
            "objective": objective,
            "blind_rules": blind_rules,
        }

    if not deck:
        return {
            "best": current,
            "discard": None,
            "recommendation": "PLAY",
            "reason": "No drawable cards remain for a replacement hand.",
            "objective": objective,
            "blind_rules": blind_rules,
        }

    if remaining_discards == 0:
        return {
            "best": current,
            "discard": None,
            "recommendation": "PLAY",
            "reason": "No discards remain.",
            "objective": objective,
            "blind_rules": blind_rules,
        }

    if remaining_discards is None:
        return {
            "best": current,
            "discard": None,
            "recommendation": "PLAY",
            "reason": "The remaining discard count is unknown.",
            "objective": objective,
            "blind_rules": blind_rules,
        }

    try:
        simulation_count = max(1, min(5000, int(simulations)))
    except (TypeError, ValueError, OverflowError):
        simulation_count = 120

    max_discard = min(5, len(hand), remaining_discards)

    if max_discard <= 0:
        return {
            "best": current,
            "discard": None,
            "recommendation": "PLAY",
            "reason": "There are no legal discards available.",
            "objective": objective,
            "blind_rules": blind_rules,
        }

    card_by_id = {
        id(card): card
        for card in hand + deck
    }

    @lru_cache(maxsize=100_000)
    def cached_evaluation(card_ids):
        cards = [card_by_id[card_id] for card_id in card_ids]
        return evaluate(cards)

    @lru_cache(maxsize=100_000)
    def cached_simulated_score(
        selected_ids,
        held_ids,
        discards_left,
        deck_left,
    ):
        selected_cards = [
            card_by_id[card_id] for card_id in selected_ids
        ]
        held_cards = [
            card_by_id[card_id] for card_id in held_ids
        ]

        evaluation = cached_evaluation(selected_ids)

        result = score_hand(
            selected_cards,
            evaluation,
            levels,
            jokers,
            held_cards,
            remaining_discards=discards_left,
            remaining_deck=deck_left,
            details=False,
            blind_rules=blind_rules,
        )

        return result["score"]

    rng = random.Random(24017)
    candidates = []

    for count in range(1, max_discard + 1):
        for indices in combinations(range(len(hand)), count):
            discarded_cards = [hand[i] for i in indices]
            discarded_index_set = set(indices)

            keep = [
                card for i, card in enumerate(hand)
                if i not in discarded_index_set
            ]

            total_score = 0
            draw_count = min(count, len(deck))

            discards_after = max(0, remaining_discards - 1)
            deck_after = max(0, len(deck) - draw_count)

            for _ in range(simulation_count):
                draw = rng.sample(deck, draw_count)
                simulated_hand = keep + draw

                simulated_ids = tuple(
                    id(card) for card in simulated_hand
                )

                best_simulated_score = 0

                if exact_cards is not None:
                    min_size = exact_cards
                    max_size = exact_cards
                else:
                    min_size = 1
                    max_size = min(5, len(simulated_hand))

                if len(simulated_hand) >= min_size:
                    for size in range(
                        min_size,
                        min(max_size, len(simulated_hand)) + 1,
                    ):
                        for chosen_indices in combinations(
                            range(len(simulated_hand)),
                            size,
                        ):
                            selected_ids = tuple(
                                simulated_ids[i]
                                for i in chosen_indices
                            )

                            selected_id_set = set(selected_ids)

                            held_ids = tuple(
                                card_id
                                for card_id in simulated_ids
                                if card_id not in selected_id_set
                            )

                            score = cached_simulated_score(
                                selected_ids,
                                held_ids,
                                discards_after,
                                deck_after,
                            )

                            if score > best_simulated_score:
                                best_simulated_score = score

                total_score += best_simulated_score

            matching_cards = (
                sum(
                    1 for card in discarded_cards
                    if _rank_number(card.get("rank")) == mail_rank
                )
                if money_mode_active
                else 0
            )

            candidates.append({
                "indices": indices,
                "cards": discarded_cards,
                "ev": total_score / simulation_count,
                "money_ev": matching_cards * 5,
                "mail_rank_count": matching_cards,
                "simulations": simulation_count,
            })

    if money_mode_active:
        discard = max(
            candidates,
            key=lambda candidate: (
                candidate["money_ev"],
                candidate["ev"],
            ),
            default=None,
        )
    else:
        discard = max(
            candidates,
            key=lambda candidate: candidate["ev"],
            default=None,
        )

    play_score = current["score"] if current else 0

    if money_mode_active:
        if discard and discard["money_ev"] > 0:
            recommendation = "DISCARD"
            count = discard["mail_rank_count"]

            reason = (
                f"Mail-In Rebate is targeting rank "
                f"{state.get('mail_rank')}. Discarding these cards "
                f"should earn an estimated ${discard['money_ev']} "
                f"from {count} matching card(s). Expected replacement "
                f"hand score: {discard['ev']:,.0f}."
            )
        else:
            recommendation = "PLAY"
            reason = (
                "There are no cards matching Mail-In Rebate's "
                f"target rank ({state.get('mail_rank')}) in your hand."
            )

    elif discard and discard["ev"] > play_score * 1.15:
        recommendation = "DISCARD"
        reason = (
            f"Estimated replacement-hand score "
            f"({discard['ev']:,.0f}) is more than 15% above "
            f"the best current play ({play_score:,.0f}). "
            f"Based on {simulation_count:,} simulations."
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

    if objective == "money" and not money_mode_active:
        reason = (
            "Money mode is selected, but Mail-In Rebate is not active "
            "or its target rank could not be read. "
            "Using score strategy instead. " + reason
        )

    return {
        "best": current,
        "discard": discard,
        "recommendation": recommendation,
        "reason": reason,
        "objective": "money" if money_mode_active else "score",
        "mail_rank": state.get("mail_rank"),
        "blind_rules": blind_rules,
    }
