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


def generate_readme(report, output_path="README.md"):
    content = "\n".join(
        [
            "# TFT TR Master+ Meta Report",
            "",
            f"Patch: {report['patch']}",
            f"Total Matches Analyzed: {report['total_matches']}",
            "",
            "## Core Statistics",
            "",
            "| Metric | Value |",
            "| --- | --- |",
            f"| Average Placement | {_float(report['average_placement'])} |",
            f"| Win Rate | {_percent(report['win_rate'])} |",
            f"| Top 4 Rate | {_percent(report['top4_rate'])} |",
            "",
            "## Most Played Traits",
            "",
            _table(report["traits_df"]),
            "",
            "## Most Played Carries",
            "",
            _table(report["carries_df"]),
            "",
            "## Most Used Items",
            "",
            _table(report["items_df"]),
            "",
        ]
    )
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(content)
