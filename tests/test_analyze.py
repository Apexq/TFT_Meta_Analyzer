import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath("/home/runner/work/TFT_Meta_Analyzer/TFT_Meta_Analyzer/src"))

from analyze import analyze_matches, build_comp_signature, format_patch_version, format_trait_name
from generate_readme import generate_readme


class AnalyzeTests(unittest.TestCase):
    def test_format_patch_version_major_minor_only(self):
        version = "Version 16.5.5512345 (Mar 01 2026/10:00:00) [PUBLIC]"
        self.assertEqual(format_patch_version(version), "16.5")

    def test_format_trait_name_human_readable(self):
        self.assertEqual(format_trait_name("TFT16_ShadowIsles"), "Shadow Isles")

    def test_build_comp_signature_sorted_and_style_filtered(self):
        traits = [
            {"name": "TFT16_Duelist", "style": 3, "num_units": 4},
            {"name": "TFT16_Ionia", "style": 4, "num_units": 6},
            {"name": "TFT16_Invoker", "style": 2, "num_units": 2},
            {"name": "TFT16_Unused", "style": 0, "num_units": 9},
        ]
        self.assertEqual(build_comp_signature(traits), "Duelist (4) + Invoker (2) + Ionia (6)")

    def test_analyze_and_readme_outputs_meta_tables(self):
        results = [
            {
                "participant": {
                    "placement": 1,
                    "traits": [
                        {"name": "TFT16_Ionia", "style": 4, "num_units": 6},
                        {"name": "TFT16_Duelist", "style": 3, "num_units": 4},
                    ],
                    "units": [
                        {"character_id": "TFT16_Ahri", "cost": 4, "itemNames": ["A", "B", "C"]},
                        {"character_id": "TFT16_Yasuo", "cost": 1, "itemNames": ["A", "B", "C"]},
                    ],
                },
                "match_info": {"game_version": "Version 16.5.5512345 (Mar 01 2026/10:00:00) [PUBLIC]"},
            },
            {
                "participant": {
                    "placement": 5,
                    "traits": [
                        {"name": "TFT16_Duelist", "style": 3, "num_units": 4},
                        {"name": "TFT16_Ionia", "style": 4, "num_units": 6},
                    ],
                    "units": [{"character_id": "TFT16_Yasuo", "cost": 1, "itemNames": ["A", "B"]}],
                },
                "match_info": {"game_version": "Version 16.5.1111111 (Mar 01 2026/11:00:00) [PUBLIC]"},
            },
        ]
        report = analyze_matches(results)

        self.assertEqual(report["patch"], "16.5")
        self.assertEqual(report["comps_df"].iloc[0]["Comp"], "Duelist (4) + Ionia (6)")
        self.assertEqual(report["carries_df"].iloc[0]["Unit"], "Ahri")

        with tempfile.NamedTemporaryFile("r+", suffix=".md") as temp_file:
            generate_readme(report, output_path=temp_file.name)
            temp_file.seek(0)
            content = temp_file.read()

        self.assertIn("Patch: 16.5", content)
        self.assertIn("| Comp | Games | Pick Rate | Avg Place | Win Rate | Top 4 Rate |", content)
        self.assertNotIn("TFT16_", content)


if __name__ == "__main__":
    unittest.main()
