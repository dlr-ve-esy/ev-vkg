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
    width = tt.Int(539).tag(sync=True)
    height = tt.Int(404).tag(sync=True)
    marker_size = tt.Int(18).tag(sync=True)
    marker_size_secondary = tt.Int(6).tag(sync=True)
    legend_marker_size = tt.Int(9).tag(sync=True)
    legend_height = tt.Int(20).tag(sync=True)

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


class FAIRCartogramWidget(anywidget.AnyWidget):
    # Widget front-end JavaScript code
    _esm = pathlib.Path("widgets/javascript/fair_score_cartogram.js")

    # Stateful property that can be accessed by JavaScript & Python
    fair_scores = tt.Dict({}).tag(sync=True)
    source_colors = tt.Dict({}).tag(sync=True)
    country_grid = tt.Dict({}).tag(sync=True)
    width = tt.Int(539).tag(sync=True)
    height = tt.Int(404).tag(sync=True)

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
