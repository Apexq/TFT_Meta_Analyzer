import re

import pandas as pd


def format_patch_version(game_version):
    if not game_version:
        return "N/A"
    match = re.search(r"(\d+)\.(\d+)", str(game_version))
    if not match:
        return "N/A"
    return f"{match.group(1)}.{match.group(2)}"


def _format_name(raw_name):
    if not raw_name:
        return ""
    value = re.sub(r"^TFT\d+_", "", str(raw_name))
    value = re.sub(r"^TFT_Item_", "", value)
    value = re.sub(r"^TFT\d+", "", value)
    value = value.replace("_", " ")
    value = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", value)
    return " ".join(part.capitalize() for part in value.split())


def format_trait_name(trait_name):
    return _format_name(trait_name)


def format_unit_name(unit_name):
    return _format_name(unit_name)


def format_item_name(item_name):
    return _format_name(item_name)


def build_comp_signature(traits):
    active_traits = []
    for trait in traits or []:
        if trait.get("style", 0) > 0 and trait.get("name"):
            active_traits.append((format_trait_name(trait["name"]), int(trait.get("num_units", 0))))
    if not active_traits:
        return "N/A"
    active_traits.sort(key=lambda value: value[0])
    return " + ".join(f"{name} ({tier})" for name, tier in active_traits)


def compute_pick_rate(games_with_entry, total_games):
    if not total_games:
        return 0.0
    return float(games_with_entry) / float(total_games)


def _aggregate(df, group_col, total_games, include_top4=False):
    if df.empty:
        columns = [group_col, "Games", "Pick Rate", "Avg Placement", "Win Rate"]
        if include_top4:
            columns.append("Top 4 Rate")
        return pd.DataFrame(columns=columns)
    grouped = (
        df.groupby(group_col, as_index=False)
        .agg(
            Games=("placement", "size"),
            AvgPlacement=("placement", "mean"),
            WinRate=("placement", lambda value: (value == 1).mean()),
            Top4Rate=("placement", lambda value: (value <= 4).mean()),
        )
        .rename(columns={"AvgPlacement": "Avg Placement", "WinRate": "Win Rate", "Top4Rate": "Top 4 Rate"})
    )
    grouped["Pick Rate"] = grouped["Games"].map(lambda games: compute_pick_rate(games, total_games))
    sort_columns = ["Pick Rate", "Avg Placement"]
    grouped = grouped.sort_values(sort_columns, ascending=[False, True], ignore_index=True)
    columns = [group_col, "Games", "Pick Rate", "Avg Placement", "Win Rate"]
    if include_top4:
        columns.append("Top 4 Rate")
    return grouped[columns]


def analyze_matches(player_match_results):
    if not player_match_results:
        empty_comp = pd.DataFrame(columns=["Comp", "Games", "Pick Rate", "Avg Placement", "Win Rate", "Top 4 Rate"])
        empty_trait = pd.DataFrame(columns=["Trait", "Games", "Pick Rate", "Avg Placement", "Win Rate"])
        empty_carry = pd.DataFrame(columns=["Unit", "Games", "Pick Rate", "Avg Placement", "Win Rate"])
        return {
            "patch": "N/A",
            "total_matches": 0,
            "comps_df": empty_comp,
            "traits_df": empty_trait,
            "carries_df": empty_carry,
        }

    patch_values = []
    rows = []
    trait_rows = []

    for result in player_match_results:
        participant = result["participant"]
        info = result.get("match_info") or result.get("info") or {}
        placement = participant.get("placement")
        if placement is None:
            continue

        patch_values.append(format_patch_version(info.get("game_version")))
        comp_signature = build_comp_signature(participant.get("traits", []))

        units = participant.get("units", [])
        carry_name = "N/A"
        if units:
            carry = max(
                units,
                key=lambda unit: (
                    len(unit.get("itemNames") or unit.get("items") or []),
                    unit.get("cost", 0),
                ),
            )
            carry_name = format_unit_name(carry.get("character_id"))

        rows.append({"placement": placement, "Comp": comp_signature, "Unit": carry_name})

        seen_traits = set()
        for trait in participant.get("traits", []):
            if trait.get("style", 0) > 0 and trait.get("name"):
                name = format_trait_name(trait["name"])
                if name not in seen_traits:
                    trait_rows.append({"placement": placement, "Trait": name})
                    seen_traits.add(name)

    df = pd.DataFrame(rows)
    total = int(len(df))
    patch_series = pd.Series([value for value in patch_values if value != "N/A"])
    patch = patch_series.value_counts().idxmax() if not patch_series.empty else "N/A"

    return {
        "patch": patch,
        "total_matches": total,
        "comps_df": _aggregate(df, "Comp", total_games=total, include_top4=True).head(10),
        "traits_df": _aggregate(pd.DataFrame(trait_rows), "Trait", total_games=total).head(10),
        "carries_df": _aggregate(df, "Unit", total_games=total).head(10),
    }
