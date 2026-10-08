from traitlets.traitlets import List
from traitlets.traitlets import Any
import pathlib
import anywidget
import traitlets as tt


class BarChartWidget(anywidget.AnyWidget):
    # Widget front-end JavaScript code
    _esm = pathlib.Path("widgets/javascript/barchart.js")

    # Stateful property that can be accessed by JavaScript & Python
    input = tt.Dict({}).tag(sync=True)
    shadow = tt.Dict({}).tag(sync=True)
    markers = tt.Dict({}).tag(sync=True)
    width = tt.Int(500).tag(sync=True)
    height = tt.Int(300).tag(sync=True)
    margin = tt.Dict({"top": 20, "right": 0, "bottom": 40, "left": 50}).tag(sync=True)
    bar_color = tt.Unicode("steelblue").tag(sync=True)
    marker_color = tt.Unicode("indianred").tag(sync=True)
    shadow_color = tt.Unicode("black").tag(sync=True)
    custom_colors = tt.Dict({}).tag(sync=True)
    bar_radius = tt.Int(5).tag(sync=True)
    y_max = tt.Int(0).tag(sync=True)
    y_ticks: List[Any] = tt.List([]).tag(sync=True)
    x_ticks: List[Any] = tt.List([]).tag(sync=True)
    y_grid: List[Any] = tt.List([]).tag(sync=True)
    x_label = tt.Unicode("").tag(sync=True)
    y_label = tt.Unicode("").tag(sync=True)
    offset = tt.Int(0).tag(sync=True)
    font_size = tt.Float(0.8).tag(sync=True)
    main_label = tt.Unicode("").tag(sync=True)
    shadow_label = tt.Unicode("").tag(sync=True)
    marker_label = tt.Unicode("").tag(sync=True)
    _css = """
    .barchart {
        display: flex;
        justify-content: center; 
        align-items: center;
        height: 100%; /* Adjust as needed */
        width: 100%; /* Adjust as needed */
        }

    .barchart svg {
        max-width: 100%;
        max-height: 100%;
        }
    """


class StackedBarChartWidget(anywidget.AnyWidget):
    # Widget front-end JavaScript code
    _esm = pathlib.Path("widgets/javascript/stacked_barchart.js")

    # Stateful property that can be accessed by JavaScript & Python
    input = tt.List([]).tag(sync=True)
    x_key = tt.Unicode("code").tag(sync=True)
    width = tt.Int(500).tag(sync=True)
    height = tt.Int(300).tag(sync=True)
    cat_colors = tt.Dict({}).tag(sync=True)
    bar_radius = tt.Int(5).tag(sync=True)
    y_max = tt.Int(0).tag(sync=True)
    y_ticks: List[Any] = tt.List([]).tag(sync=True)
    x_ticks: List[Any] = tt.List([]).tag(sync=True)
    y_grid: List[Any] = tt.List([]).tag(sync=True)
    x_label = tt.Unicode("").tag(sync=True)
    y_label = tt.Unicode("").tag(sync=True)
    offset = tt.Int(0).tag(sync=True)
    legend = tt.Bool(False).tag(sync=True)
    font_size = tt.Float(0.8).tag(sync=True)
    _css = """
    .barchart {
        display: flex;
        justify-content: center; 
        align-items: center;
        height: 100%; /* Adjust as needed */
        width: 100%; /* Adjust as needed */
        }

    .barchart svg {
        max-width: 100%;
        max-height: 100%;
        }
    """


class DoubleStackedBarChartWidget(anywidget.AnyWidget):
    # Widget front-end JavaScript code
    _esm = pathlib.Path("widgets/javascript/double_stacked_barchart.js")

    # Stateful property that can be accessed by JavaScript & Python
    input_a = tt.List([]).tag(sync=True)
    input_b = tt.List([]).tag(sync=True)
    x_key = tt.Unicode("code").tag(sync=True)
    width = tt.Int(500).tag(sync=True)
    height = tt.Int(300).tag(sync=True)
    margin = tt.Dict({"top": 20, "right": 0, "bottom": 40, "left": 50}).tag(sync=True)
    cat_colors = tt.Dict({}).tag(sync=True)
    # Hatch pattern per band colour for greyscale legibility.
    cat_hatches = tt.Dict({}).tag(sync=True)
    bar_radius = tt.Int(5).tag(sync=True)
    y_max = tt.Int(0).tag(sync=True)
    y_ticks: List[Any] = tt.List([]).tag(sync=True)
    x_ticks: List[Any] = tt.List([]).tag(sync=True)
    y_grid: List[Any] = tt.List([]).tag(sync=True)
    x1_label = tt.Unicode("").tag(sync=True)
    x2_label = tt.Unicode("").tag(sync=True)
    y_label = tt.Unicode("").tag(sync=True)
    offset = tt.Int(0).tag(sync=True)
    font_size = tt.Float(0.8).tag(sync=True)
    legend_item_width = tt.Float(10.0).tag(sync=True)

    _css = """
    .barchart-double {
        display: flex;
        justify-content: center; 
        align-items: center;
        height: 100%; /* Adjust as needed */
        width: 100%; /* Adjust as needed */
        }

    .barchart-double svg {
        max-width: 100%;
        max-height: 100%;
        }
    """


class FAIRBarChartsWidget(anywidget.AnyWidget):
    # Widget front-end JavaScript code
    _esm = pathlib.Path("widgets/javascript/fair_score_barcharts.js")

    # Stateful property that can be accessed by JavaScript & Python
    fair_scores = tt.Dict({}).tag(sync=True)
    source_colors = tt.Dict({}).tag(sync=True)
    width = tt.Int(700).tag(sync=True)
    height = tt.Int(640).tag(sync=True)
    bar_radius = tt.Int(4).tag(sync=True)
    font_size = tt.Float(0.8).tag(sync=True)

    _css = """
    .fair-barcharts {
        display: flex;
        justify-content: center; 
        align-items: center;
        height: 100%; /* Adjust as needed */
        width: 100%; /* Adjust as needed */
        }

    .fair-barcharts svg {
        max-width: 100%;
        max-height: 100%;
        }
    """


class FAIRDatasetScoresWidget(anywidget.AnyWidget):
    """Stacked FAIR scores per dataset (Table 8 unit), hatched fills."""

    # Widget front-end JavaScript code
    _esm = pathlib.Path("widgets/javascript/fair_dataset_scores.js")

    # Stateful property that can be accessed by JavaScript & Python
    input = tt.List([]).tag(sync=True)
    width = tt.Int(539).tag(sync=True)
    height = tt.Int(320).tag(sync=True)
    margin = tt.Dict({"top": 20, "right": 10, "bottom": 80, "left": 40}).tag(sync=True)
    bar_radius = tt.Int(4).tag(sync=True)
    font_size = tt.Float(0.9).tag(sync=True)
    y_max = tt.Int(12).tag(sync=True)
    y_ticks = tt.List([3, 6, 9, 12]).tag(sync=True)
    y_grid = tt.List([3, 6, 9, 12]).tag(sync=True)
    y_label = tt.Unicode("FAIR score").tag(sync=True)
    colors = tt.Dict(
        {"F": "#6181ab", "A": "#e0ba2f", "I": "#c8433e", "R": "#73a861"}
    ).tag(sync=True)
    dimension_labels = tt.Dict(
        {
            "F": "Findability",
            "A": "Accessibility",
            "I": "Interoperability",
            "R": "Reusability",
        }
    ).tag(sync=True)
    legend_item_width = tt.Float(7.8).tag(sync=True)

    _css = """
    .fair-datasets {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100%;
        width: 100%;
        }

    .fair-datasets svg {
        max-width: 100%;
        max-height: 100%;
        }
    """


class GroupedBarChartWidget(anywidget.AnyWidget):
    """Grouped side-by-side bars (e.g. calculated vs EAFO reference)."""

    # Widget front-end JavaScript code
    _esm = pathlib.Path("widgets/javascript/grouped_barchart.js")

    # Stateful property that can be accessed by JavaScript & Python
    input = tt.Dict({}).tag(sync=True)
    shadow = tt.Dict({}).tag(sync=True)
    markers = tt.Dict({}).tag(sync=True)
    width = tt.Int(500).tag(sync=True)
    height = tt.Int(300).tag(sync=True)
    margin = tt.Dict({"top": 20, "right": 0, "bottom": 40, "left": 50}).tag(sync=True)
    bar_color = tt.Unicode("#0173b2").tag(sync=True)
    marker_color = tt.Unicode("#353839").tag(sync=True)
    shadow_color = tt.Unicode("#d55e00").tag(sync=True)
    bar_radius = tt.Int(4).tag(sync=True)
    y_max = tt.Int(0).tag(sync=True)
    y_ticks = tt.List([]).tag(sync=True)
    y_grid = tt.List([]).tag(sync=True)
    x_label = tt.Unicode("").tag(sync=True)
    y_label = tt.Unicode("").tag(sync=True)
    offset = tt.Int(0).tag(sync=True)
    font_size = tt.Float(0.8).tag(sync=True)
    main_label = tt.Unicode("").tag(sync=True)
    shadow_label = tt.Unicode("").tag(sync=True)
    marker_label = tt.Unicode("").tag(sync=True)

    _css = """
    .barchart {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100%;
        width: 100%;
        }

    .barchart svg {
        max-width: 100%;
        max-height: 100%;
        }
    """
