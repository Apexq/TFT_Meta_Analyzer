def _percent(value):
    if value is None:
        return "N/A"
    return f"{value * 100:.2f}%"


def _float(value):
    if value is None:
        return "N/A"
    return f"{value:.2f}"


def _table(df):
    if df.empty:
        columns = list(df.columns)
        return f"| {' | '.join(columns)} |\n| {' | '.join(['---'] * len(columns))} |"
    columns = list(df.columns)
    lines = [
        f"| {' | '.join(columns)} |",
        f"| {' | '.join(['---'] * len(columns))} |",
    ]
    for row in df.itertuples(index=False):
        lines.append(f"| {' | '.join(str(value) for value in row)} |")
    return "\n".join(lines)


def _format_report_table(df):
    if df.empty:
        return df
    formatted = df.copy()
    for column in ["Pick Rate", "Win Rate", "Top 4 Rate"]:
        if column in formatted:
            formatted[column] = formatted[column].map(_percent)
    for column in ["Avg Placement", "Avg Place"]:
        if column in formatted:
            formatted[column] = formatted[column].map(_float)
    return formatted


def generate_readme(report, output_path="README.md"):
    comps_df = _format_report_table(report["comps_df"]).rename(columns={"Avg Placement": "Avg Place"})
    traits_df = _format_report_table(report["traits_df"]).rename(columns={"Avg Placement": "Avg Place"})
    carries_df = _format_report_table(report["carries_df"]).rename(columns={"Avg Placement": "Avg Place"})

    content = "\n".join(
        [
            "# TFT TR Master+ Meta Report",
            "",
            f"Patch: {report['patch']}",
            f"Total Games Analyzed: {report['total_matches']}",
            "",
            "## Top Meta Comps",
            "",
            _table(comps_df),
            "",
            "## Trait Performance",
            "",
            _table(traits_df),
            "",
            "## Top Carries",
            "",
            _table(carries_df),
            "",
        ]
    )
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(content)
