"""Virtual knowledge graph (VKG) methodology schematic widget.

`VkgSchematicWidget` is an anywidget rendering the two-branch methodology
schematic in the notebook (front-end code in
`widgets/javascript/vkg_schematic.js`). The layout mirrors the manuscript
figure built by the repo-root `vkg_schematic.py` (Methodology section,
Knowledge Graph Analysis subsection): the reviewed EVCI data sources on
the left feed two branches -- the FAIR assessment of the sources (upper
lane) and the harmonisation-and-querying pipeline over the acquired
datasets (lower lane) -- and both feed the integrated assessment on the
right.

Importing the module only needs anywidget and traitlets; the manuscript
figure itself is built with matplotlib by the standalone script.
"""

import pathlib

import anywidget
import traitlets as tt


class VkgSchematicWidget(anywidget.AnyWidget):
    # Widget front-end JavaScript code
    _esm = pathlib.Path("widgets/javascript/vkg_schematic.js")

    # Stateful properties that can be accessed by JavaScript & Python
    width = tt.Int(890).tag(sync=True)
    height = tt.Int(340).tag(sync=True)
    font_size = tt.Float(1.0).tag(sync=True)
    labels = tt.Dict(
        {
            "sources_title": "EVCI data sources",
            "sources_note": "reviewed in NAPs\n& registries",
            "sources_count": "(33 countries)",
            "evidence": "Metadata &\naccess evidence",
            "fair_title": "FAIR assessment",
            "fair_note": "(F/A/I/R scores)",
            "acquired_title": "Datasets acquired",
            "acquired_note": "(23 datasets)",
            "acquired_aside": "remaining sources listed\nbut not accessible",
            "parsing_title": "Parsing & mappings",
            "parsing_note": "(maplib, OTTR, CHIO)",
            "panel_title": "Virtual knowledge graph",
            "panel_note": "materialised in memory\n(no persistent triple store)",
            "indicators_title": "Monitoring\nindicators",
            "indicators_note": "(SPARQL, Listing 1;\neight per country)",
            "comparison_title": "Fidelity\ncomparison",
            "comparison_note": "(N/A if no reference\nor failed analysis)",
            "reference_title": "EAFO reports",
            "reference_note": "(June 2025 reference)",
            "assessment_title": "Integrated\nassessment",
            "assessment_note": "(four groups)",
        }
    ).tag(sync=True)
    colors = tt.Dict(
        {
            "ink": "#353839",
            "source": "#0173B2",
            "mapping": "#DE8F05",
            "ontology": "#9D6B92",
            "graph": "#029E73",
        }
    ).tag(sync=True)
    # Motif nodes in panel-normalized coordinates ([-1, 1] on both axes):
    # a hub with four satellite nodes, edges as pairs of node indices.
    motif_nodes = tt.List(
        [
            [0.0, -0.176],
            [-0.428, 0.094],
            [-0.428, -0.447],
            [0.428, 0.094],
            [0.428, -0.447],
        ]
    ).tag(sync=True)
    motif_edges = tt.List(
        [
            [0, 1],
            [0, 2],
            [0, 3],
            [0, 4],
        ]
    ).tag(sync=True)
    # Geometry below is expressed in the internal design units of the figure
    # (1 unit = 1 cm at the original manuscript scale).
    node_radius = tt.Float(0.09).tag(sync=True)
    box_rounding = tt.Float(0.07).tag(sync=True)
    line_width = tt.Float(0.7).tag(sync=True)
    _css = """
    .schematic {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100%; /* Adjust as needed */
        width: 100%; /* Adjust as needed */
        }

    .schematic svg {
        max-width: 100%;
        max-height: 100%;
        }
    """
