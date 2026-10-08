import * as d3 from "https://esm.sh/d3@7";

// Layout in design units (1 unit = 1 cm at the original manuscript scale),
// mirroring the manuscript figure built by the repo-root vkg_schematic.py:
// the reviewed sources on the left feed two branches -- the FAIR assessment
// of the sources (upper lane) and the harmonisation-and-querying pipeline
// over the acquired datasets (lower lane) -- and both feed the integrated
// assessment on the right.
const VIEW = { x: -0.15, y: -4.05, w: 17.8, h: 6.85 };

const SRC = { cx: 1.3, cy: 0.0, w: 2.4, h: 3.8 };
const UPPER_Y = 2.0;
const LOWER_Y = -2.0;
const EVIDENCE = { cx: 4.6, w: 2.3, h: 1.1 };
const FAIR = { cx: 7.8, w: 2.5, h: 1.1 };
const ACQUIRED = { cx: 4.6, w: 2.3, h: 1.1 };
const PARSING = { cx: 7.8, w: 2.5, h: 1.1 };
const PANEL = { cx: 11.1, w: 2.9, h: 1.7 };
const INDICATORS = { cx: 14.0, w: 2.2, h: 1.2 };
const COMPARISON = { cx: 16.35, w: 2.1, h: 1.3 };
const REFERENCE = { cx: 16.35, cy: -3.55, w: 2.1, h: 0.85 };
const ASSESSMENT = { cx: 16.35, cy: 1.0, w: 2.5, h: 1.7 };

// 1 PostScript point expressed in design units.
const PT = 0.0353;

async function render({ model, el }) {
  const container = document.createElement("div");
  container.classList.add("schematic");
  el.appendChild(container);

  renderSchematic(d3.select(container), {
    width: model.get("width"),
    height: model.get("height"),
    fontSize: model.get("font_size"),
    labels: model.get("labels"),
    colors: model.get("colors"),
    motifNodes: model.get("motif_nodes"),
    motifEdges: model.get("motif_edges"),
    nodeRadius: model.get("node_radius"),
    boxRounding: model.get("box_rounding"),
    lineWidth: model.get("line_width"),
  });
}

function renderSchematic(container, cfg) {
  const {
    width,
    height,
    fontSize,
    labels,
    colors,
    motifNodes,
    motifEdges,
    nodeRadius,
    boxRounding,
    lineWidth,
  } = cfg;

  const svg = container
    .append("svg")
    .attr("width", width)
    .attr("height", height)
    .attr("viewBox", `${VIEW.x} ${VIEW.y} ${VIEW.w} ${VIEW.h}`)
    .attr("preserveAspectRatio", "xMidYMid meet");

  svg
    .append("defs")
    .append("marker")
    .attr("id", "schematic-arrow")
    .attr("viewBox", "0 0 10 10")
    .attr("refX", 9.5)
    .attr("refY", 5)
    .attr("markerWidth", 0.24)
    .attr("markerHeight", 0.24)
    .attr("markerUnits", "userSpaceOnUse")
    .attr("orient", "auto-start-reverse")
    .append("path")
    .attr("d", "M 0 0 L 10 5 L 0 10 z")
    .attr("fill", colors.ink);

  const box = (b, cy, fill, { rounding = boxRounding, dashed = false } = {}) =>
    svg
      .append("rect")
      .attr("x", b.cx - b.w / 2)
      .attr("y", cy - b.h / 2)
      .attr("width", b.w)
      .attr("height", b.h)
      .attr("rx", rounding)
      .attr("ry", rounding)
      .attr("fill", fill)
      .attr("stroke", colors.ink)
      .attr("stroke-width", lineWidth * PT)
      .attr("stroke-dasharray", dashed ? "0.07 0.07" : null);

  const arrow = (x1, y1, x2, y2, dashed = false) =>
    svg
      .append("line")
      .attr("x1", x1)
      .attr("y1", y1)
      .attr("x2", x2)
      .attr("y2", y2)
      .attr("stroke", colors.ink)
      .attr("stroke-width", 0.6 * PT)
      .attr("stroke-dasharray", dashed ? "0.07 0.07" : null)
      .attr("marker-end", "url(#schematic-arrow)");

  // Text as centered lines; fit(w, h) shrinks the font until the block
  // fits the given box, mirroring the measured fit of the figure version.
  const makeText = (spec) => {
    spec.size = spec.size || 7;
    spec.weight = spec.weight || "bold";
    spec.fill = spec.fill || colors.ink;
    spec.style = spec.style || "normal";
    const t = svg
      .append("text")
      .attr("text-anchor", "middle")
      .attr("dominant-baseline", "central")
      .attr("font-family", "Tinos, serif")
      .attr("font-weight", spec.weight)
      .attr("font-style", spec.style)
      .attr("fill", spec.fill);
    const layout = () => {
      const lines = spec.str.split("\n");
      const lh = spec.size * PT * fontSize * 1.25;
      const y0 = spec.y - (lh * (lines.length - 1)) / 2;
      t.attr("font-size", spec.size * PT * fontSize)
        .selectAll("tspan")
        .data(lines)
        .join("tspan")
        .attr("x", spec.x)
        .attr("y", (d, i) => y0 + i * lh)
        .text((d) => d);
    };
    layout();
    return {
      fit: (w, h, fitPad = 0.96) => {
        try {
          const bb = t.node().getBBox();
          const scale = Math.min(
            1,
            fitPad * (w / Math.max(bb.width, 0.001)),
            fitPad * (h / Math.max(bb.height, 0.001))
          );
          if (scale < 1) {
            spec.size = spec.size * scale;
            layout();
          }
        } catch (err) {
          // getBBox needs a rendered element; skip the fit if unavailable.
        }
      },
    };
  };

  // -- left: the reviewed sources (common starting point) -------------------
  box(SRC, SRC.cy, colors.source);
  makeText({
    x: SRC.cx,
    y: 0.75,
    str: labels.sources_title,
    fill: "white",
  }).fit(SRC.w - 0.3, 0.6);
  makeText({
    x: SRC.cx,
    y: 0.05,
    str: labels.sources_note,
    size: 6,
    weight: "normal",
    fill: "white",
  }).fit(SRC.w - 0.3, 1.0);
  makeText({
    x: SRC.cx,
    y: -0.95,
    str: labels.sources_count,
    size: 5.5,
    weight: "normal",
    fill: "white",
  }).fit(SRC.w - 0.3, 0.5);

  // -- upper lane: FAIR assessment branch -----------------------------------
  arrow(SRC.cx + SRC.w / 2, 1.2, EVIDENCE.cx - EVIDENCE.w / 2, UPPER_Y);
  box(EVIDENCE, UPPER_Y, "white");
  makeText({
    x: EVIDENCE.cx,
    y: UPPER_Y,
    str: labels.evidence,
  }).fit(EVIDENCE.w, EVIDENCE.h);

  arrow(EVIDENCE.cx + EVIDENCE.w / 2, UPPER_Y, FAIR.cx - FAIR.w / 2, UPPER_Y);
  box(FAIR, UPPER_Y, colors.ontology);
  makeText({
    x: FAIR.cx,
    y: UPPER_Y + 0.18,
    str: labels.fair_title,
    fill: "white",
  }).fit(FAIR.w, 0.55);
  makeText({
    x: FAIR.cx,
    y: UPPER_Y - 0.25,
    str: labels.fair_note,
    size: 5.5,
    weight: "normal",
    fill: "white",
  }).fit(FAIR.w, 0.45);

  // -- lower lane: harmonisation and querying branch ------------------------
  arrow(SRC.cx + SRC.w / 2, -1.2, ACQUIRED.cx - ACQUIRED.w / 2, LOWER_Y);
  box(ACQUIRED, LOWER_Y, colors.source);
  makeText({
    x: ACQUIRED.cx,
    y: LOWER_Y + 0.16,
    str: labels.acquired_title,
    fill: "white",
  }).fit(ACQUIRED.w, 0.55);
  makeText({
    x: ACQUIRED.cx,
    y: LOWER_Y - 0.26,
    str: labels.acquired_note,
    size: 5.5,
    weight: "normal",
    fill: "white",
  }).fit(ACQUIRED.w, 0.45);
  makeText({
    x: ACQUIRED.cx,
    y: -2.95,
    str: labels.acquired_aside,
    size: 5,
    weight: "normal",
    style: "italic",
  });

  arrow(ACQUIRED.cx + ACQUIRED.w / 2, LOWER_Y, PARSING.cx - PARSING.w / 2, LOWER_Y);
  box(PARSING, LOWER_Y, colors.mapping);
  makeText({
    x: PARSING.cx,
    y: LOWER_Y + 0.16,
    str: labels.parsing_title,
    fill: "white",
  }).fit(PARSING.w, 0.55);
  makeText({
    x: PARSING.cx,
    y: LOWER_Y - 0.26,
    str: labels.parsing_note,
    size: 5.5,
    weight: "normal",
    fill: "white",
  }).fit(PARSING.w, 0.45);

  arrow(PARSING.cx + PARSING.w / 2, LOWER_Y, PANEL.cx - PANEL.w / 2, LOWER_Y);
  box(PANEL, LOWER_Y, "white", { rounding: boxRounding * 1.4 });
  makeText({
    x: PANEL.cx,
    y: -1.45,
    str: labels.panel_title,
    size: 6.5,
  }).fit(PANEL.w - 0.3, 0.5);

  // Compact motif inside the VKG panel: a hub with satellite nodes, in
  // panel-normalized coordinates ([-1, 1] on both axes).
  const nodes = motifNodes.map(([u, v]) => [
    PANEL.cx + u * (PANEL.w / 2),
    LOWER_Y + v * (PANEL.h / 2),
  ]);
  motifEdges.forEach(([i, j]) => {
    svg
      .append("line")
      .attr("x1", nodes[i][0])
      .attr("y1", nodes[i][1])
      .attr("x2", nodes[j][0])
      .attr("y2", nodes[j][1])
      .attr("stroke", colors.ink)
      .attr("stroke-width", 0.5 * PT)
      .attr("stroke-linecap", "round");
  });
  nodes.forEach(([nx, ny]) => {
    svg
      .append("circle")
      .attr("cx", nx)
      .attr("cy", ny)
      .attr("r", nodeRadius)
      .attr("fill", colors.graph)
      .attr("stroke", colors.ink)
      .attr("stroke-width", 0.5 * PT);
  });
  makeText({
    x: PANEL.cx,
    y: -2.62,
    str: labels.panel_note,
    size: 5,
    weight: "normal",
    style: "italic",
  }).fit(PANEL.w - 0.3, 0.6);

  arrow(PANEL.cx + PANEL.w / 2, LOWER_Y, INDICATORS.cx - INDICATORS.w / 2, LOWER_Y);
  box(INDICATORS, LOWER_Y, "white");
  makeText({
    x: INDICATORS.cx,
    y: LOWER_Y + 0.28,
    str: labels.indicators_title,
  }).fit(INDICATORS.w, 0.7);
  makeText({
    x: INDICATORS.cx,
    y: LOWER_Y - 0.32,
    str: labels.indicators_note,
    size: 5,
    weight: "normal",
  }).fit(INDICATORS.w, 0.6);

  // -- comparison with its separate EAFO reference input --------------------
  arrow(INDICATORS.cx + INDICATORS.w / 2, LOWER_Y, COMPARISON.cx - COMPARISON.w / 2, LOWER_Y);
  box(COMPARISON, LOWER_Y, colors.ink);
  makeText({
    x: COMPARISON.cx,
    y: LOWER_Y + 0.28,
    str: labels.comparison_title,
    fill: "white",
  }).fit(COMPARISON.w, 0.7);
  makeText({
    x: COMPARISON.cx,
    y: LOWER_Y - 0.38,
    str: labels.comparison_note,
    size: 5,
    weight: "normal",
    fill: "white",
  }).fit(COMPARISON.w, 0.6);

  box(REFERENCE, REFERENCE.cy, "white", { dashed: true });
  makeText({
    x: REFERENCE.cx,
    y: REFERENCE.cy + 0.14,
    str: labels.reference_title,
  }).fit(REFERENCE.w, 0.45);
  makeText({
    x: REFERENCE.cx,
    y: REFERENCE.cy - 0.18,
    str: labels.reference_note,
    size: 5,
    weight: "normal",
  }).fit(REFERENCE.w, 0.4);
  arrow(
    REFERENCE.cx,
    REFERENCE.cy + REFERENCE.h / 2,
    COMPARISON.cx,
    LOWER_Y - COMPARISON.h / 2,
    true
  );

  // -- right: integrated assessment receives both branches ------------------
  box(ASSESSMENT, ASSESSMENT.cy, colors.graph);
  makeText({
    x: ASSESSMENT.cx,
    y: ASSESSMENT.cy + 0.3,
    str: labels.assessment_title,
    fill: "white",
  }).fit(ASSESSMENT.w, 0.8);
  makeText({
    x: ASSESSMENT.cx,
    y: ASSESSMENT.cy - 0.45,
    str: labels.assessment_note,
    size: 5.5,
    weight: "normal",
    fill: "white",
  }).fit(ASSESSMENT.w, 0.5);
  arrow(FAIR.cx + FAIR.w / 2, UPPER_Y, ASSESSMENT.cx - ASSESSMENT.w / 2, ASSESSMENT.cy + 0.3);
  arrow(COMPARISON.cx, LOWER_Y + COMPARISON.h / 2, ASSESSMENT.cx, ASSESSMENT.cy - ASSESSMENT.h / 2);
}

export default { render };
