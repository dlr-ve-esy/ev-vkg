import * as d3 from "https://esm.sh/d3@7";

// Layout in design units (1 unit = 1 cm at the original manuscript scale).
// The reviewed sources on the left feed two branches -- the FAIR
// assessment of the sources and the harmonisation-and-querying pipeline
// over the acquired datasets -- and both converge into the integrated
// assessment on the right. The lanes funnel towards the assessment: the
// boxes descend in cy from the source side to the assessment side, so
// the space between the branches narrows towards the right instead of
// forming an empty band across the middle of the figure.
const VIEW = { x: -0.15, y: -3.2, w: 17.9, h: 5.85 };

const SRC = { cx: 1.3, cy: 0.0, w: 2.4, h: 4.9 };
// Pipeline branch (upper lane in design coordinates).
const ACQUIRED = { cx: 4.5, cy: -1.85, w: 2.2, h: 1.3 };
const PARSING = { cx: 7.5, cy: -1.6, w: 2.3, h: 1.3 };
const PANEL = { cx: 10.6, cy: -1.3, w: 2.7, h: 1.7 };
const INDICATORS = { cx: 13.55, cy: -0.95, w: 2.0, h: 1.3 };
const COMPARISON = { cx: 16.15, cy: -0.75, w: 2.0, h: 1.3 };
// FAIR branch (lower lane in design coordinates).
const EVIDENCE = { cx: 4.5, cy: 1.75, w: 2.3, h: 1.3 };
const FAIR = { cx: 7.7, cy: 1.5, w: 2.4, h: 1.3 };
const SCORES = { cx: 11.0, cy: 1.1, w: 2.5, h: 1.3 };
// Separate EAFO reference input below the fidelity comparison, and the
// integrated assessment receiving both branches.
const REFERENCE = { cx: 16.15, cy: -2.2, w: 2.0, h: 0.8 };
const ASSESSMENT = { cx: 16.35, cy: 1.3, w: 2.5, h: 1.9 };

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

  const box = (b, fill, { rounding = boxRounding, dashed = false } = {}) =>
    svg
      .append("rect")
      .attr("x", b.cx - b.w / 2)
      .attr("y", b.cy - b.h / 2)
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

  // Two-line box label: bold title above a smaller note.
  const label = (b, title, note, { fill = colors.ink } = {}) => {
    makeText({
      x: b.cx,
      y: b.cy + 0.22,
      str: title,
      fill,
    }).fit(b.w, 0.55);
    makeText({
      x: b.cx,
      y: b.cy - 0.32,
      str: note,
      size: 5.5,
      weight: "normal",
      fill,
    }).fit(b.w, 0.45);
  };

  // -- left: the reviewed sources (common starting point) -------------------
  box(SRC, colors.source);
  makeText({
    x: SRC.cx,
    y: 1.2,
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
    y: -1.15,
    str: labels.sources_count,
    size: 5.5,
    weight: "normal",
    fill: "white",
  }).fit(SRC.w - 0.3, 0.5);

  // -- pipeline branch: acquired datasets to fidelity comparison ------------
  // Both branch arrows fan out from the middle of the sources box, so
  // the wedge between the lanes reads as the branching point.
  arrow(SRC.cx + SRC.w / 2, -0.5, ACQUIRED.cx - ACQUIRED.w / 2, ACQUIRED.cy);
  box(ACQUIRED, colors.source);
  label(ACQUIRED, labels.acquired_title, labels.acquired_note, {
    fill: "white",
  });
  makeText({
    x: ACQUIRED.cx,
    y: -2.72,
    str: labels.acquired_aside,
    size: 5,
    weight: "normal",
    style: "italic",
  });

  arrow(
    ACQUIRED.cx + ACQUIRED.w / 2,
    ACQUIRED.cy,
    PARSING.cx - PARSING.w / 2,
    PARSING.cy
  );
  box(PARSING, colors.mapping);
  label(PARSING, labels.parsing_title, labels.parsing_note, {
    fill: "white",
  });

  arrow(
    PARSING.cx + PARSING.w / 2,
    PARSING.cy,
    PANEL.cx - PANEL.w / 2,
    PANEL.cy
  );
  box(PANEL, "white", { rounding: boxRounding * 1.4 });
  makeText({
    x: PANEL.cx,
    y: PANEL.cy + 0.55,
    str: labels.panel_title,
    size: 6.5,
  }).fit(PANEL.w - 0.3, 0.5);

  // Compact motif inside the VKG panel: a hub with satellite nodes, in
  // panel-normalized coordinates ([-1, 1] on both axes).
  const nodes = motifNodes.map(([u, v]) => [
    PANEL.cx + u * (PANEL.w / 2),
    PANEL.cy + v * (PANEL.h / 2),
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
    y: PANEL.cy - 0.65,
    str: labels.panel_note,
    size: 5,
    weight: "normal",
    style: "italic",
  }).fit(PANEL.w - 0.3, 0.6);

  arrow(
    PANEL.cx + PANEL.w / 2,
    PANEL.cy,
    INDICATORS.cx - INDICATORS.w / 2,
    INDICATORS.cy
  );
  box(INDICATORS, "white");
  label(INDICATORS, labels.indicators_title, labels.indicators_note);

  arrow(
    INDICATORS.cx + INDICATORS.w / 2,
    INDICATORS.cy,
    COMPARISON.cx - COMPARISON.w / 2,
    COMPARISON.cy
  );
  box(COMPARISON, colors.ink);
  label(COMPARISON, labels.comparison_title, labels.comparison_note, {
    fill: "white",
  });

  // -- FAIR branch: evidence to per-dataset scores ---------------------------
  arrow(SRC.cx + SRC.w / 2, 0.5, EVIDENCE.cx - EVIDENCE.w / 2, EVIDENCE.cy);
  box(EVIDENCE, "white");
  makeText({
    x: EVIDENCE.cx,
    y: EVIDENCE.cy,
    str: labels.evidence,
  }).fit(EVIDENCE.w, EVIDENCE.h);

  arrow(
    EVIDENCE.cx + EVIDENCE.w / 2,
    EVIDENCE.cy,
    FAIR.cx - FAIR.w / 2,
    FAIR.cy
  );
  box(FAIR, colors.ontology);
  label(FAIR, labels.fair_title, labels.fair_note, { fill: "white" });

  arrow(FAIR.cx + FAIR.w / 2, FAIR.cy, SCORES.cx - SCORES.w / 2, SCORES.cy);
  box(SCORES, "white");
  label(SCORES, labels.scores_title, labels.scores_note);

  // -- separate EAFO reference input ----------------------------------------
  box(REFERENCE, "white", { dashed: true });
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
    COMPARISON.cy - COMPARISON.h / 2,
    true
  );

  // -- right: integrated assessment receives both branches ------------------
  box(ASSESSMENT, colors.graph);
  makeText({
    x: ASSESSMENT.cx,
    y: ASSESSMENT.cy + 0.35,
    str: labels.assessment_title,
    fill: "white",
  }).fit(ASSESSMENT.w, 0.8);
  makeText({
    x: ASSESSMENT.cx,
    y: ASSESSMENT.cy - 0.5,
    str: labels.assessment_note,
    size: 5.5,
    weight: "normal",
    fill: "white",
  }).fit(ASSESSMENT.w, 0.5);
  arrow(
    SCORES.cx + SCORES.w / 2,
    SCORES.cy,
    ASSESSMENT.cx - ASSESSMENT.w / 2,
    ASSESSMENT.cy + 0.35
  );
  arrow(
    COMPARISON.cx,
    COMPARISON.cy + COMPARISON.h / 2,
    ASSESSMENT.cx,
    ASSESSMENT.cy - ASSESSMENT.h / 2
  );
}

export default { render };
