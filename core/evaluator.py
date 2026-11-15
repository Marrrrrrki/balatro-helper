from __future__ import annotations
from collections import Counter
from itertools import combinations

HAND_ORDER = [
    "Flush Five", "Flush House", "Five of a Kind", "Straight Flush",
    "Four of a Kind", "Full House", "Flush", "Straight",
    "Three of a Kind", "Two Pair", "Pair", "High Card"
]

def rank_value(card):
    return int(card.get("rank", 0) or 0)

def is_flush(cards):
    suits = [c.get("suit") for c in cards if c.get("enhancement") != "m_stone"]
    return len(suits) == len(cards) and len(set(suits)) == 1

def straight_high(ranks):
    unique = set(r for r in ranks if r > 0)
    if len(unique) != len(ranks):
        return None
    if 14 in unique:
        unique.add(1)
    for high in sorted(unique, reverse=True):
        needed = set(range(high - 4, high + 1))
        if needed.issubset(unique):
            return high
    return None

def evaluate(cards):
    """Evaluate a selected 1-5 card set. Returns poker type, scored cards and tie-break."""
    if not cards:
        return {"name":"No hand", "scoring_cards":[], "tie":(), "strength":-1}
    ranks = [rank_value(c) for c in cards if c.get("enhancement") != "m_stone"]
    counts = Counter(ranks)
    groups = sorted(((n, r) for r, n in counts.items()), reverse=True)
    flush = is_flush(cards)
    shigh = straight_high(ranks) if len(ranks) == len(cards) else None
    n = len(cards)

    if n == 5 and len(counts) == 1 and flush:
        name = "Flush Five"
        scoring = list(cards)
        tie = tuple(ranks)
    elif n == 5 and sorted(counts.values()) == [2,3] and flush:
        name = "Flush House"
        scoring = list(cards)
        tie = tuple(r for _,r in groups)
    elif n == 5 and len(counts) == 1:
        name = "Five of a Kind"
        scoring = list(cards)
        tie = tuple(ranks)
    elif n == 5 and flush and shigh:
        name = "Straight Flush"
        scoring = list(cards)
        tie = (shigh,)
    elif groups and groups[0][0] == 4:
        name = "Four of a Kind"
        scoring = [c for c in cards if rank_value(c) == groups[0][1]]
        tie = (groups[0][1],)
    elif n == 5 and sorted(counts.values()) == [2,3]:
        name = "Full House"
        scoring = list(cards)
        tie = tuple(r for _,r in groups)
    elif n >= 5 and flush:
        name = "Flush"
        scoring = list(cards)
        tie = tuple(sorted(ranks, reverse=True))
    elif n == 5 and shigh:
        name = "Straight"
        scoring = list(cards)
        tie = (shigh,)
    elif groups and groups[0][0] == 3:
        name = "Three of a Kind"
        scoring = [c for c in cards if rank_value(c) == groups[0][1]]
        tie = (groups[0][1],)
    elif sum(1 for ncount,_ in groups if ncount == 2) >= 2:
        pair_ranks = [r for ncount,r in groups if ncount == 2][:2]
        name = "Two Pair"
        scoring = [c for c in cards if rank_value(c) in pair_ranks]
        tie = tuple(pair_ranks)
    elif groups and groups[0][0] == 2:
        name = "Pair"
        scoring = [c for c in cards if rank_value(c) == groups[0][1]]
        tie = (groups[0][1],)
    else:
        name = "High Card"
        high = max(ranks or [0])
        scoring = [c for c in cards if rank_value(c) == high][:1]
        tie = (high,)
    return {"name":name, "scoring_cards":scoring, "tie":tie, "strength":HAND_ORDER.index(name)}

def best_play(hand, hand_levels, score_fn):
    best = None
    for size in range(1, min(5, len(hand)) + 1):
        for chosen in combinations(hand, size):
            ev = evaluate(list(chosen))
            result = score_fn(list(chosen), ev, hand_levels)
            candidate = {"cards":list(chosen), "evaluation":ev, **result}
            if best is None or candidate["score"] > best["score"]:
                best = candidate
    return best
