import pathlib
import anywidget
import traitlets as tt


class SourcesCartogramWidget(anywidget.AnyWidget):
    # Widget front-end JavaScript code
    _esm = pathlib.Path("widgets/javascript/sources_cartogram.js")

    # Stateful property that can be accessed by JavaScript & Python
    sources_per_country = tt.Dict({}).tag(sync=True)
    source_colors = tt.Dict({}).tag(sync=True)
    color_legend = tt.Dict({}).tag(sync=True)
    country_grid = tt.Dict({}).tag(sync=True)
    _css = """
    .cartogram {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100%; /* Adjust as needed */
        width: 100%; /* Adjust as needed */
        }

    .cartogram svg {
        max-width: 100%;
        max-height: 100%;
        }
    """
