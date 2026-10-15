"""The exporter must use supplied calculations, including updated results."""
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from export_widget_pngs import build_specs, export_paper_figures, merge_capacities


class FigureExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def write(self, name, value):
        (self.root / f"{name}.json").write_text(json.dumps(value))

    def test_changed_results_reach_widget_without_manuscript_constraints(self):
        self.write("results", [{"Code": "ZZ", "total_accounted_power": 45678, "total_mw": 56789}])
        self.write("filtered_markers", {"ZZ": 67890})
        widget = build_specs(["results_plot"], self.root)[0]["widget"]
        self.assertEqual(widget.input, {"ZZ": 45678})
        self.assertEqual(widget.shadow, {"ZZ": 56789})
        self.assertEqual(widget.markers, {"ZZ": 67890})
        self.assertGreater(widget.y_max, 67890)

    def test_fair_scores_are_loaded_from_current_run(self):
        row = {"code": "new.1", "F": 1, "A": 2, "I": 3, "R": 1, "TOTAL": 7}
        self.write("fair_scores_datasets", [row])
        widget = build_specs(["fair_dataset_scores"], self.root)[0]["widget"]
        self.assertEqual(widget.input, [row])

    def test_static_figures_do_not_require_query_results(self):
        specs = build_specs(["sources_cartogram", "vkg_schematic"], self.root)
        self.assertEqual([s["name"] for s in specs], ["sources_cartogram", "vkg_schematic"])

    def test_missing_calculations_have_actionable_error(self):
        with self.assertRaisesRegex(FileNotFoundError, "Run main.py"):
            build_specs(["results_plot"], self.root)

    def test_partial_paper_export_does_not_copy_stale_figures(self):
        (self.root / "sources_cartogram.png").write_bytes(b"new")
        (self.root / "results_plot.png").write_bytes(b"stale")
        export_paper_figures(self.root, {"sources_cartogram.png"})
        self.assertEqual((self.root / "paper/figure_1.png").read_bytes(), b"new")
        self.assertFalse((self.root / "paper/figure_4.png").exists())

    def test_capacity_panels_merge_in_order(self):
        Image.new("RGB", (10, 3), "red").save(self.root / "capacities_above_400mw.png")
        Image.new("RGB", (10, 4), "blue").save(self.root / "capacities_below_400mw.png")
        with Image.open(merge_capacities(self.root)) as merged:
            self.assertEqual(merged.size, (10, 7))
            self.assertEqual(merged.getpixel((0, 0)), (255, 0, 0))
            self.assertEqual(merged.getpixel((0, 6)), (0, 0, 255))


if __name__ == "__main__":
    unittest.main()
