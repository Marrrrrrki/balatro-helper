
from __future__ import annotations

import os
import time
import zlib
from pathlib import Path

from .lua_parser import parse_lua_table


def decode_jkr(path: Path | str) -> dict:
    path = Path(path)
    data = path.read_bytes()

    if not data:
        raise ValueError("The save file is empty.")

    if data.startswith(b"return"):
        raw = data.decode("utf-8")
    else:
        try:
            raw = zlib.decompress(data, -15).decode("utf-8")
        except Exception as exc:
            raise ValueError(
                f"Could not decompress this .jkr file: {exc}"
            ) from exc

    return parse_lua_table(raw)


def read_jkr_retry(
    path: Path | str,
    attempts: int = 4,
    delay: float = 0.15,
) -> dict:
    last_error = None

    for _ in range(attempts):
        try:
            return decode_jkr(path)
        except Exception as exc:
            last_error = exc
            time.sleep(delay)

    raise ValueError(
        f"Could not read a stable save file: {last_error}"
    )


def find_steam_save() -> Path | None:
    appdata = os.environ.get("APPDATA")
    candidates = []

    if appdata:
        base = Path(appdata) / "Balatro"

        if base.exists():
            for profile in base.iterdir():
                candidate = profile / "save.jkr"

                if candidate.is_file():
                    candidates.append(candidate)

    if not candidates:
        return None

    return max(candidates, key=lambda p: p.stat().st_mtime)


def sorted_cards(area: dict) -> list[dict]:
    cards = area.get("cards", {}) if isinstance(area, dict) else {}

    if isinstance(cards, list):
        return cards

    if isinstance(cards, dict):
        return [
            value
            for _, value in sorted(
                cards.items(),
                key=lambda item: (
                    (0, item[0])
                    if isinstance(item[0], int)
                    else (1, str(item[0]))
                ),
            )
        ]

    return []


def card_from_save(raw: dict) -> dict:
    base = raw.get("base", {}) or {}
    ability = raw.get("ability", {}) or {}
    save_fields = raw.get("save_fields", {}) or {}

    center = save_fields.get("center", "")
    rank_name = base.get("value", "Unknown")

    rank_map = {
        "Ace": 14,
        "King": 13,
        "Queen": 12,
        "Jack": 11,
    }

    try:
        rank = rank_map.get(str(rank_name), int(rank_name))
    except (ValueError, TypeError):
        rank = rank_map.get(str(rank_name), 0)

    return {
        "name": base.get("name", "Unknown card"),
        "rank": rank,
        "rank_name": rank_name,
        "suit": base.get("suit", "Unknown"),
        "center": center,
        "enhancement": (
            center if center and center != "c_base" else "Base"
        ),
        "edition": (
            (raw.get("edition") or {}).get("type")
            if isinstance(raw.get("edition"), dict)
            else None
        ),
        "seal": raw.get("seal"),
        "debuff": bool(raw.get("debuff", False)),
        "ability": ability,
        "raw": raw,
    }


def extract_mail_rank(current_round: dict):
    mail_card = current_round.get("mail_card")

    if mail_card is None:
        return None

    if isinstance(mail_card, dict):
        base = mail_card.get("base", {}) or {}

        value = (
            mail_card.get("rank")
            or mail_card.get("id")
            or mail_card.get("value")
            or base.get("value")
            or base.get("id")
        )
    else:
        value = mail_card

    rank_names = {
        "Ace": 14,
        "King": 13,
        "Queen": 12,
        "Jack": 11,
    }

    if str(value) in rank_names:
        return rank_names[str(value)]

    try:
        rank = int(value)
        return rank if 2 <= rank <= 14 else None
    except (TypeError, ValueError):
        return None


def extract_blind_key(blind: dict):
    """Find the internal blind key across common save-data layouts."""
    if not isinstance(blind, dict):
        return None

    config = blind.get("config", {}) or {}
    config_blind = config.get("blind", {}) or {}

    candidates = [
        blind.get("key"),
        blind.get("id"),
        config_blind.get("key"),
        config_blind.get("id"),
        config.get("key"),
    ]

    for value in candidates:
        if isinstance(value, str) and value.strip():
            return value.strip()

    return None


def extract_state(root: dict) -> dict:
    areas = root.get("cardAreas", {}) or {}
    game = root.get("GAME", {}) or {}
    current = game.get("current_round", {}) or {}
    resets = game.get("round_resets", {}) or {}
    hand_levels = game.get("hands", {}) or {}

    hand = [
        card_from_save(card)
        for card in sorted_cards(areas.get("hand", {}))
    ]

    deck = [
        card_from_save(card)
        for card in sorted_cards(areas.get("deck", {}))
    ]

    jokers = sorted_cards(areas.get("jokers", {}))
    blind = root.get("BLIND", {}) or {}

    return {
        "version": root.get("VERSION", "Unknown"),
        "blind_name": blind.get("name", "Unknown blind"),
        "blind_key": extract_blind_key(blind),
        "blind_target": blind.get("chips", 0),
        "ante": resets.get("ante", "?"),
        "hands_left": current.get(
            "hands_left",
            resets.get("hands", "?"),
        ),
        "discards_left": current.get(
            "discards_left",
            resets.get("discards", "?"),
        ),
        "dollars": current.get(
            "dollars",
            game.get("dollars", "?"),
        ),
        "mail_rank": extract_mail_rank(current),
        "hand": hand,
        "deck": deck,
        "jokers": jokers,
        "hand_levels": hand_levels,
        "back_name": (
            root.get("BACK", {}) or {}
        ).get("name", "Unknown deck"),
        "raw": root,
    }
