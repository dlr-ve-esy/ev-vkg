import pathlib
import anywidget
import traitlets as tt


class HeatMapWidget(anywidget.AnyWidget):
    # Widget front-end JavaScript code
    _esm = pathlib.Path("widgets/javascript/heatmap.js")

    # Stateful property that can be accessed by JavaScript & Python
    input = tt.List([]).tag(sync=True)
    x_axis = tt.Unicode("").tag(sync=True)
    y_axis = tt.Unicode("").tag(sync=True)
    c_axis = tt.Unicode("").tag(sync=True)
    c_max = tt.Int().tag(sync=True)
    c_min = tt.Int().tag(sync=True)
    width = tt.Int(500).tag(sync=True)
    height = tt.Int(300).tag(sync=True)
    margin = tt.Dict({"top": 20, "right": 0, "bottom": 40, "left": 50}).tag(sync=True)
    colors = tt.Dict({}).tag(sync=True)
    base_color = tt.Unicode("#ece4df").tag(sync=True)
    cell_size = tt.Int(20).tag(sync=True)
    radius = tt.Int(5).tag(sync=True)
    x_padding = tt.Float(0.2).tag(sync=True)
    y_padding = tt.Float(0.2).tag(sync=True)
    x_label = tt.Unicode("").tag(sync=True)
    y_label = tt.Unicode("").tag(sync=True)
    font_size = tt.Float(0.8).tag(sync=True)
    invert_c = tt.Bool(False).tag(sync=True)
    _css = """
    .heatmap {
        display: flex;
        justify-content: center; 
        align-items: center;
        height: 100%; /* Adjust as needed */
        width: 100%; /* Adjust as needed */
        }

    .heatmap svg {
        max-width: 100%;
        max-height: 100%;
        }
    """
