import pathlib
import anywidget
import traitlets as tt


class GridScatterWidget(anywidget.AnyWidget):
    # Widget front-end JavaScript code
    _esm = pathlib.Path("widgets/javascript/grid_scatter.js")

    # Stateful property that can be accessed by JavaScript & Python
    input = tt.List([]).tag(sync=True)
    x_axis = tt.Unicode("").tag(sync=True)
    y_axis = tt.Unicode("").tag(sync=True)
    x_domain = tt.List([]).tag(sync=True)
    y_domain = tt.List([]).tag(sync=True)
    color_col = tt.Unicode("").tag(sync=True)
    width = tt.Int(500).tag(sync=True)
    height = tt.Int(300).tag(sync=True)
    margin = tt.Dict({"top": 20, "right": 0, "bottom": 40, "left": 50}).tag(sync=True)
    colors = tt.Dict({}).tag(sync=True)
    base_color = tt.Unicode("#b8b0ac").tag(sync=True)
    cell_size = tt.Int(20).tag(sync=True)
    radius = tt.Int(5).tag(sync=True)
    x_padding = tt.Float(0.2).tag(sync=True)
    y_padding = tt.Float(0.2).tag(sync=True)
    x_label = tt.Unicode("").tag(sync=True)
    y_label = tt.Unicode("").tag(sync=True)
    font_size = tt.Float(0.8).tag(sync=True)
    cell_ycorrection =  tt.Int(0).tag(sync=True)
    _css = """
    .scatter {
        display: flex;
        justify-content: center; 
        align-items: center;
        height: 100%; /* Adjust as needed */
        width: 100%; /* Adjust as needed */
        }

    .scatter svg {
        max-width: 100%;
        max-height: 100%;
        }
    """
