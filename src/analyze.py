from collections import Counter

import pandas as pd


def _top_rows(counter, key_name, limit=10):
    rows = counter.most_common(limit)
    if not rows:
        return pd.DataFrame(columns=[key_name, "Count"])
    return pd.DataFrame(rows, columns=[key_name, "Count"])


def analyze_matches(player_match_results):
    if not player_match_results:
        empty = pd.DataFrame(columns=["Trait", "Count"])
        return {
            "patch": "N/A",
            "total_matches": 0,
            "average_placement": None,
            "win_rate": None,
            "top4_rate": None,
            "traits_df": empty,
            "carries_df": pd.DataFrame(columns=["Unit", "Count"]),
            "items_df": pd.DataFrame(columns=["Item", "Count"]),
        }

    placements = []
    trait_counter = Counter()
    carry_counter = Counter()
    item_counter = Counter()
    patch_counter = Counter()

    for result in player_match_results:
        participant = result["participant"]
        info = result["match_info"]
        placements.append(participant.get("placement"))

        version = info.get("game_version", "")
        if version:
            patch_counter[".".join(version.split(".")[:3])] += 1

        traits = participant.get("traits", [])
        active_traits = sorted(
            trait.get("name")
            for trait in traits
            if trait.get("tier_current", 0) > 0 and trait.get("name")
        )
        if active_traits:
            trait_counter[" + ".join(active_traits)] += 1

        units = participant.get("units", [])
        if units:
            carry = max(
                units,
                key=lambda unit: (
                    len(unit.get("itemNames") or unit.get("items") or []),
                    unit.get("tier", 0),
                    unit.get("rarity", 0),
                ),
            )
            carry_name = carry.get("character_id")
            if carry_name:
                carry_counter[carry_name] += 1

            for unit in units:
                item_names = unit.get("itemNames")
                if item_names:
                    item_counter.update(item_names)
                else:
                    item_ids = unit.get("items") or []
                    item_counter.update(str(item_id) for item_id in item_ids)

    placements_series = pd.Series(placements).dropna()
    total = int(len(placements_series))

    return {
        "patch": patch_counter.most_common(1)[0][0] if patch_counter else "N/A",
        "total_matches": total,
        "average_placement": float(placements_series.mean()) if total else None,
        "win_rate": float((placements_series == 1).mean()) if total else None,
        "top4_rate": float((placements_series <= 4).mean()) if total else None,
        "traits_df": _top_rows(trait_counter, "Trait"),
        "carries_df": _top_rows(carry_counter, "Unit"),
        "items_df": _top_rows(item_counter, "Item"),
    }
