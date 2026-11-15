from __future__ import annotations
from itertools import combinations
import random
from .evaluator import best_play, evaluate
from .scoring import score_hand

def analyze(state, simulations=120):
    hand = state["hand"]
    levels = state["hand_levels"]
    jokers = state["jokers"]
    deck = state["deck"]

    def scorer(chosen, ev, hand_levels):
        held = [c for c in hand if c not in chosen]
        return score_hand(chosen, ev, hand_levels, jokers, held)

    current = best_play(hand, levels, scorer)
    if not hand or not deck:
        return {"best": current, "discard": None, "recommendation": "PLAY", "reason": "No drawable cards remain."}

    # Estimate discard EV by replacing 1-5 cards, then choosing the best play
    # from the resulting hand. This is an approximation, not a full game-state solver.
    rng = random.Random(24017)
    max_discard = min(5, len(hand))
    candidates = []
    for count in range(1, max_discard + 1):
        for indices in combinations(range(len(hand)), count):
            keep = [c for i,c in enumerate(hand) if i not in indices]
            total = 0
            for _ in range(simulations):
                draw = rng.sample(deck, min(count, len(deck)))
                simulated = keep + draw
                best_score = 0
                for size in range(1, min(5, len(simulated)) + 1):
                    for chosen in combinations(simulated, size):
                        ev = evaluate(list(chosen))
                        held = [c for c in simulated if c not in chosen]
                        score = score_hand(list(chosen), ev, levels, jokers, held)["score"]
                        if score > best_score:
                            best_score = score
                total += best_score
            avg = total / simulations
            candidates.append({"indices":indices, "cards":[hand[i] for i in indices], "ev":avg})
    discard = max(candidates, key=lambda x:x["ev"]) if candidates else None
    play_score = current["score"] if current else 0
    if discard and discard["ev"] > play_score * 1.15 and state.get("discards_left", 0) not in (0, "?", None):
        recommendation = "DISCARD"
        reason = f"Estimated replacement-hand score ({discard['ev']:,.0f}) is meaningfully above the best current play ({play_score:,.0f})."
    else:
        recommendation = "PLAY"
        reason = f"The best current play ({play_score:,.0f}) is at least as attractive as the estimated discard outcome ({discard['ev']:,.0f} if available)."
    return {"best":current, "discard":discard, "recommendation":recommendation, "reason":reason}
