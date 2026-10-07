"""Virtual knowledge graph (VKG) methodology schematic.

This module has two roles:

1. `VkgSchematicWidget`, an anywidget rendering the schematic in the
   notebook (front-end code in `widgets/javascript/vkg_schematic.js`).
   Importing the module only needs anywidget and traitlets; matplotlib is
   not required and is imported lazily by the build code below.

2. The build script for the manuscript figure (Methodology section,
   Knowledge Graph Analysis subsection), written next to this file as
   `vkg_schematic.pdf`, with a 300-dpi PNG twin for the raster figure set.

Run the build with uv (installs matplotlib into an ephemeral environment):

    uv run widgets/vkg_schematic.py

or with any Python that already has matplotlib:

    python widgets/vkg_schematic.py

The design matches the other figures of the manuscript (Observable Plot
exports): a Times-compatible serif (Tinos/Times) and the seaborn
"colorblind" palette sampled from the SVG sources of the existing figures.
"""

import pathlib

import anywidget
import traitlets as tt


class VkgSchematicWidget(anywidget.AnyWidget):
    # Widget front-end JavaScript code
    _esm = pathlib.Path("widgets/javascript/vkg_schematic.js")

    # Stateful property that can be accessed by JavaScript & Python
    width = tt.Int(890).tag(sync=True)
    height = tt.Int(320).tag(sync=True)
    font_size = tt.Float(1.0).tag(sync=True)
    sources = tt.List(
        [
            "DATEX II profiles",
            "OCPI",
            "OICP",
            "NOBIL API",
            "National formats",
        ]
    ).tag(sync=True)
    labels = tt.Dict(
        {
            "sources_title": "Heterogeneous\ndata sources",
            "mapping_title": "Per-source\nmapping modules",
            "mapping": "maplib + OTTR",
            "ontology_abbr": "CHIO",
            "ontology_name": "Charging\nInfrastructure\nOntology",
            "ontology_note": "(shared vocabulary)",
            "panel_title": "Virtual knowledge graph",
            "panel_note": "instantiated at query time\n(no RDF materialized)",
            "query_title": "SPARQL query",
            "query_note": "(Listing 1; identical\nfor all sources)",
            "query_time": "query time",
            "quantities": "Relevant\nquantities",
            "quantities_note": "(eight, per country)",
            "fidelity": "Comparison against\nEAFO reports",
            "fidelity_note": "(fidelity assessment)",
        }
    ).tag(sync=True)
    colors = tt.Dict(
        {
            "ink": "#353839",
            "source": "#0173B2",
            "mapping": "#DE8F05",
            "ontology": "#9D6B92",
            "query": "#D55E00",
            "graph": "#029E73",
        }
    ).tag(sync=True)
    # Motif nodes in normalized panel coordinates ([-1, 1] on both axes),
    # edges as pairs of node indices.
    motif_nodes = tt.List(
        [
            [-0.054, 0.091],
            [-0.541, 0.545],
            [-0.459, -0.455],
            [0.432, 0.5],
            [0.486, -0.545],
            [-0.649, -0.045],
            [0.649, -0.045],
        ]
    ).tag(sync=True)
    motif_edges = tt.List(
        [
            [0, 1],
            [0, 2],
            [0, 3],
            [0, 4],
            [1, 5],
            [2, 5],
            [3, 6],
            [4, 6],
        ]
    ).tag(sync=True)
    # Geometry below is expressed in the internal design units of the figure
    # (1 unit = 1 cm at the original manuscript scale).
    node_radius = tt.Float(0.09).tag(sync=True)
    stack_spacing = tt.Float(0.8).tag(sync=True)
    column_gap = tt.Float(0.5).tag(sync=True)
    query_gap = tt.Float(0.8).tag(sync=True)
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
