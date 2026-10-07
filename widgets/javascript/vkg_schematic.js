import * as d3 from "https://esm.sh/d3@7";

// Box sizes in design units (1 unit = 1 cm at the original manuscript scale).
const BOXES = {
  source: { w: 2.3, h: 0.6 },
  mapping: { w: 2.05, h: 0.6 },
  ontology: { w: 1.8, h: 2.6 },
  panel: { w: 3.7, h: 3.5 },
  query: { w: 3.0, h: 0.85 },
  quantities: { w: 2.3, h: 0.95 },
  fidelity: { w: 2.55, h: 1.15 },
};

// 1 PostScript point expressed in design units.
const PT = 0.0353;

async function render({ model, el }) {
  const width = model.get("width");
  const height = model.get("height");
  const fontSize = model.get("font_size");
  const sources = model.get("sources");
  const labels = model.get("labels");
  const colors = model.get("colors");
  const motifNodes = model.get("motif_nodes");
  const motifEdges = model.get("motif_edges");
  const nodeRadius = model.get("node_radius");
  const stackSpacing = model.get("stack_spacing");
  const columnGap = model.get("column_gap");
  const queryGap = model.get("query_gap");
  const boxRounding = model.get("box_rounding");
  const lineWidth = model.get("line_width");

  let continer = document.createElement("div");
  continer.classList.add("schematic");

  const body = d3.select(continer);

  el.appendChild(continer);

  renderSchematic(
    body,
    sources,
    labels,
    colors,
    motifNodes,
    motifEdges,
    width,
    height,
    fontSize,
    nodeRadius,
    stackSpacing,
    columnGap,
    queryGap,
    boxRounding,
    lineWidth
  );
}

function renderSchematic(
  container,
  sources,
  labels,
  colors,
  motifNodes,
  motifEdges,
  width,
  height,
  fontSize,
  nodeRadius,
  stackSpacing,
  columnGap,
  queryGap,
  boxRounding,
  lineWidth
) {
  const n = sources.length;
  const ys = d3.range(n).map((i) => (i - (n - 1) / 2) * stackSpacing);
  const stackTop = ys[n - 1] + BOXES.source.h / 2;

  // Column centers, placed left to right from the box widths and the gap.
  let x = BOXES.source.w / 2;
  const cx = { source: x };
  x += BOXES.source.w / 2 + columnGap + BOXES.mapping.w / 2;
  cx.mapping = x;
  x += BOXES.mapping.w / 2 + columnGap + BOXES.ontology.w / 2;
  cx.ontology = x;
  x += BOXES.ontology.w / 2 + columnGap + BOXES.panel.w / 2;
  cx.panel = x;
  x += BOXES.panel.w / 2 + columnGap + BOXES.quantities.w / 2;
  cx.quantities = x;
  x += BOXES.quantities.w / 2 + columnGap + BOXES.fidelity.w / 2;
  cx.fidelity = x;
  const rightEdge = x + BOXES.fidelity.w / 2;

  // Vertical anchors.
  const titleY = stackTop + 0.45;
  const panelTop = BOXES.panel.h / 2;
  const panelBottom = -BOXES.panel.h / 2;
  const panelTitleY = panelTop - 0.35;
  const panelNoteY = panelBottom + 0.5;
  const queryTop = panelBottom - queryGap;
  const queryCy = queryTop - BOXES.query.h / 2;
  const queryBottom = queryCy - BOXES.query.h / 2;

  // Vertical band available to the motif, between title and note.
  const bandTop = panelTitleY - 0.2;
  const bandBottom = panelNoteY + 0.25;
  const bandCy = (bandTop + bandBottom) / 2;
  const bandHalf = (bandTop - bandBottom) / 2;

  // Content bounds plus padding define the viewBox, so the drawing scales
  // uniformly (and keeps its proportions) inside the width x height box.
  const pad = 0.15;
  const top = titleY + 0.35;
  const bottom = queryBottom;
  const vbWidth = rightEdge + 2 * pad;
  const vbHeight = top - bottom + 2 * pad;

  const svg = container
    .append("svg")
    .attr("width", width)
    .attr("height", height)
    .attr("viewBox", `${-pad} ${bottom - pad} ${vbWidth} ${vbHeight}`)
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

  const box = (cxp, cyp, w, h, fill, rounding) =>
    svg
      .append("rect")
      .attr("x", cxp - w / 2)
      .attr("y", cyp - h / 2)
      .attr("width", w)
      .attr("height", h)
      .attr("rx", rounding)
      .attr("ry", rounding)
      .attr("fill", fill)
      .attr("stroke", colors.ink)
      .attr("stroke-width", lineWidth * PT);

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
    spec.anchor = spec.anchor || "middle";
    spec.style = spec.style || "normal";
    const t = svg
      .append("text")
      .attr("text-anchor", spec.anchor)
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

  // -- column 1: heterogeneous data sources -------------------------------
  ys.forEach((y, i) => {
    box(cx.source, y, BOXES.source.w, BOXES.source.h, colors.source, boxRounding);
    makeText({ x: cx.source, y: y, str: sources[i], fill: "white" }).fit(
      BOXES.source.w,
      BOXES.source.h
    );
  });
  makeText({ x: cx.source, y: titleY, str: labels.sources_title });

  // -- column 2: per-source mapping modules -------------------------------
  const srcRight = cx.source + BOXES.source.w / 2;
  const mapLeft = cx.mapping - BOXES.mapping.w / 2;
  const mapRight = cx.mapping + BOXES.mapping.w / 2;
  ys.forEach((y) => {
    arrow(srcRight, y, mapLeft, y);
    box(cx.mapping, y, BOXES.mapping.w, BOXES.mapping.h, colors.mapping, boxRounding);
    makeText({ x: cx.mapping, y: y, str: labels.mapping, fill: "white" }).fit(
      BOXES.mapping.w,
      BOXES.mapping.h
    );
  });
  makeText({ x: cx.mapping, y: titleY, str: labels.mapping_title });

  // -- column 3: shared ontology -----------------------------------------
  const ontoLeft = cx.ontology - BOXES.ontology.w / 2;
  const ontoRight = cx.ontology + BOXES.ontology.w / 2;
  const inset = 0.3;
  const spread = BOXES.ontology.h - 2 * inset;
  ys.forEach((y, i) => {
    const target = n > 1 ? (i - (n - 1) / 2) * (spread / (n - 1)) : 0;
    arrow(mapRight, y, ontoLeft, target);
  });
  box(cx.ontology, 0, BOXES.ontology.w, BOXES.ontology.h, colors.ontology, boxRounding);
  makeText({
    x: cx.ontology,
    y: 0.5,
    str: labels.ontology_abbr,
    size: 8,
    fill: "white",
  }).fit(BOXES.ontology.w, 0.6);
  makeText({
    x: cx.ontology,
    y: 0.02,
    str: labels.ontology_name,
    size: 5.5,
    weight: "normal",
    fill: "white",
  }).fit(BOXES.ontology.w, 0.9);
  makeText({
    x: cx.ontology,
    y: -0.52,
    str: labels.ontology_note,
    size: 5.5,
    weight: "normal",
    fill: "white",
  }).fit(BOXES.ontology.w, 0.5);

  // -- column 4: virtual knowledge graph panel ---------------------------
  arrow(ontoRight, 0, cx.panel - BOXES.panel.w / 2, 0);
  box(cx.panel, 0, BOXES.panel.w, BOXES.panel.h, "white", boxRounding * 1.4);
  makeText({
    x: cx.panel,
    y: panelTitleY,
    str: labels.panel_title,
    size: 8,
  }).fit(BOXES.panel.w - 0.4, 0.5);

  const nodes = motifNodes.map(([u, v]) => [
    cx.panel + u * (BOXES.panel.w / 2),
    bandCy + v * bandHalf,
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
    x: cx.panel,
    y: panelNoteY,
    str: labels.panel_note,
    size: 5.5,
    weight: "normal",
    style: "italic",
  }).fit(BOXES.panel.w - 0.4, 0.7);

  // -- the query enters at query time (dashed) ---------------------------
  box(cx.panel, queryCy, BOXES.query.w, BOXES.query.h, colors.query, boxRounding);
  makeText({
    x: cx.panel,
    y: queryCy + BOXES.query.h * 0.33,
    str: labels.query_title,
    fill: "white",
  }).fit(BOXES.query.w, BOXES.query.h * 0.5);
  makeText({
    x: cx.panel,
    y: queryCy - BOXES.query.h * 0.08,
    str: labels.query_note,
    size: 5.5,
    weight: "normal",
    fill: "white",
  }).fit(BOXES.query.w, BOXES.query.h * 0.7);
  arrow(cx.panel, queryTop, cx.panel, panelBottom, true);
  makeText({
    x: cx.panel + 0.15,
    y: (panelBottom + queryTop) / 2,
    str: labels.query_time,
    size: 5.5,
    weight: "normal",
    style: "italic",
    anchor: "start",
  });

  // -- outputs -------------------------------------------------------------
  const panelRight = cx.panel + BOXES.panel.w / 2;
  const quantLeft = cx.quantities - BOXES.quantities.w / 2;
  const quantRight = cx.quantities + BOXES.quantities.w / 2;
  arrow(panelRight, 0, quantLeft, 0);
  box(cx.quantities, 0, BOXES.quantities.w, BOXES.quantities.h, "white", boxRounding);
  makeText({
    x: cx.quantities,
    y: BOXES.quantities.h * 0.11,
    str: labels.quantities,
  }).fit(BOXES.quantities.w, BOXES.quantities.h * 0.7);
  makeText({
    x: cx.quantities,
    y: -BOXES.quantities.h * 0.32,
    str: labels.quantities_note,
    size: 5.5,
    weight: "normal",
  }).fit(BOXES.quantities.w, BOXES.quantities.h * 0.5);

  arrow(quantRight, 0, cx.fidelity - BOXES.fidelity.w / 2, 0);
  box(cx.fidelity, 0, BOXES.fidelity.w, BOXES.fidelity.h, colors.ink, boxRounding);
  makeText({
    x: cx.fidelity,
    y: BOXES.fidelity.h * 0.13,
    str: labels.fidelity,
    fill: "white",
  }).fit(BOXES.fidelity.w, BOXES.fidelity.h * 0.7);
  makeText({
    x: cx.fidelity,
    y: -BOXES.fidelity.h * 0.28,
    str: labels.fidelity_note,
    size: 5.5,
    weight: "normal",
    fill: "white",
  }).fit(BOXES.fidelity.w, BOXES.fidelity.h * 0.5);
}

export default { render };
