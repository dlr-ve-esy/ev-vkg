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
