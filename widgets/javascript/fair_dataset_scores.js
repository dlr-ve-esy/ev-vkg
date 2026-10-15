import * as d3 from "https://esm.sh/d3@7";

async function render({ model, el }) {
  const input = model.get("input");
  const width = model.get("width");
  const height = model.get("height");
  const margin = model.get("margin");
  const barRadius = model.get("bar_radius");
  const fontSize = model.get("font_size");
  const yTicks = model.get("y_ticks");
  const yGrid = model.get("y_grid");
  const yLabel = model.get("y_label");
  const colors = model.get("colors");
  const dimensionLabels = model.get("dimension_labels");
  const legendItemWidth = model.get("legend_item_width");
  var yMax = model.get("y_max");

  let continer = document.createElement("div");
  continer.classList.add("fair-datasets");
  el.appendChild(continer);
  const body = d3.select(continer);

  const svg = body.append("svg").attr("width", width).attr("height", height);

  const keys = ["F", "A", "I", "R"];
  const stack = d3.stack().keys(keys);
  const series = stack(input);

  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;

  const xScale = d3
    .scaleBand()
    .domain(input.map((d) => d.code))
    .range([0, innerWidth])
    .padding(0.25);

  if (!yMax || yMax === 0) {
    yMax = d3.max(series, (s) => d3.max(s, (d) => d[1]));
  }
  const yScale = d3
    .scaleLinear()
    .domain([0, yMax])
    .nice()
    .range([innerHeight, 0]);

  const chartGroup = svg
    .append("g")
    .attr("transform", `translate(${margin.left}, ${margin.top})`);

  // Greyscale fills with hatching: one pattern per dimension, the
  // background colour ordered by luminance so the segments stay
  // legible in black and white print.
  const fill = addHatchDefs(svg, keys, colors);

  const y_grid = d3.axisLeft(yScale).tickSize(-innerWidth).tickFormat("");
  if (yGrid.length > 0) {
    y_grid.tickValues(yGrid);
  }
  const axis = chartGroup.append("g").attr("class", "y-grid");
  axis.call(y_grid).attr("stroke-opacity", 0.2);
  axis.selectAll("path").style("opacity", 0);

  // Rounded top clip per bar.
  chartGroup
    .selectAll("clipPath")
    .data(input)
    .join("clipPath")
    .attr("id", (d) => `clip-fair-${d.code}`)
    .append("path")
    .attr("d", (d) => {
      const x = xScale(d.code);
      const barWidth = xScale.bandwidth();
      const y = yScale(d.TOTAL);
      const barHeight = innerHeight - y;
      return `
        M${x},${y + barRadius}
        Q${x},${y} ${x + barRadius},${y}
        L${x + barWidth - barRadius},${y}
        Q${x + barWidth},${y} ${x + barWidth},${y + barRadius}
        L${x + barWidth},${y + barHeight}
        L${x},${y + barHeight}
        Z
      `;
    });

  // Stacked segments, one series per FAIR dimension.
  chartGroup
    .selectAll("g.stack")
    .data(series)
    .join("g")
    .attr("class", "stack")
    .each(function (s) {
      d3.select(this)
        .selectAll("rect")
        .data(s)
        .join("rect")
        .attr("x", (d, i) => xScale(input[i].code))
        .attr("y", (d) => yScale(d[1]))
        .attr("height", (d) => Math.max(yScale(d[0]) - yScale(d[1]), 0))
        .attr("width", xScale.bandwidth())
        .attr("clip-path", (d, i) => `url(#clip-fair-${input[i].code})`)
        .attr("fill", fill[s.key]);
    });

  // X axis with rotated dataset codes.
  const x_axis = chartGroup
    .append("g")
    .attr("transform", `translate(0, ${innerHeight})`);

  x_axis
    .call(d3.axisBottom(xScale).tickSize(0).tickPadding(4))
    .selectAll("text")
    .style("text-anchor", "end")
    .attr("dx", "-0.2em")
    .attr("dy", "0.4em")
    .attr("transform", `rotate(-45)`)
    .style("font-family", "Tinos, serif")
    .style("font-size", `${fontSize * 0.8}rem`);
  x_axis.selectAll("path").style("opacity", 0.8);

  const y_axis = d3.axisLeft(yScale).tickSize(0).tickPadding(6);
  if (yTicks.length > 0) {
    y_axis.tickValues(yTicks);
  }
  const y_axis_ticks = chartGroup.append("g");
  y_axis_ticks
    .call(y_axis)
    .style("font-family", "Tinos, serif")
    .style("font-size", `${fontSize * 0.8}rem`);
  y_axis_ticks.selectAll("path").style("opacity", 0);

  if (yLabel.length > 0) {
    chartGroup
      .append("text")
      .attr("text-anchor", "start")
      .attr("y", -6)
      .attr("x", 0)
      .style("font-family", "Tinos, serif")
      .attr("font-size", `${fontSize}rem`)
      .text(yLabel);
  }

  // Legend below the rotated labels.
  const legendGroup = svg
    .append("g")
    .attr("class", "legend")
    .attr(
      "transform",
      `translate(${margin.left}, ${height - margin.bottom + 34})`
    );
  const legendSquareSize = convertRemToPixels(fontSize * 0.9);
  const itemWidth = legendItemWidth * convertRemToPixels(fontSize);

  legendGroup
    .selectAll(".legend-item")
    .data(keys)
    .join("g")
    .attr("class", "legend-item")
    .attr("transform", (d, i) => `translate(${i * itemWidth}, 0)`)
    .each(function (key) {
      const legendItem = d3.select(this);
      legendItem
        .append("rect")
        .attr("width", legendSquareSize)
        .attr("height", legendSquareSize)
        .attr("rx", 2)
        .attr("y", -legendSquareSize / 2)
        .attr("fill", fill[key])
        .attr("stroke", "#4a4a4a")
        .attr("stroke-width", 0.5);
      legendItem
        .append("text")
        .text(dimensionLabels[key] || key)
        .attr("x", legendSquareSize + 4)
        .attr("y", legendSquareSize / 8)
        .attr("dominant-baseline", "middle")
        .style("font-family", "Tinos, serif")
        .attr("font-size", `${fontSize * 0.8}rem`);
    });
}

// One SVG pattern per dimension: luminance-ordered grey background plus
// a hatch so the segments survive greyscale printing.
function addHatchDefs(svg, keys, colors) {
  const hatches = { F: "none", A: "diag", I: "cross", R: "dot" };
  const defs = svg.append("defs");
  const fill = {};
  keys.forEach((key, i) => {
    const color = colors[key] || "#888888";
    const hatch = hatches[key] || "none";
    if (hatch === "none") {
      fill[key] = color;
      return;
    }
    const id = `fair-hatch-${key}`;
    const pattern = defs
      .append("pattern")
      .attr("id", id)
      .attr("width", 6)
      .attr("height", 6)
      .attr("patternUnits", "userSpaceOnUse");
    pattern
      .append("rect")
      .attr("width", 6)
      .attr("height", 6)
      .attr("fill", color);
    const line = luminance(color) > 0.55 ? "#4a4a4a" : "#ffffff";
    const stroke = pattern
      .append("path")
      .attr("d", hatchPath(hatch))
      .attr("stroke", line)
      .attr("stroke-width", 1.1);
    fill[key] = `url(#${id})`;
  });
  return fill;
}

function hatchPath(hatch) {
  switch (hatch) {
    case "diag":
      return "M0,6 L6,0";
    case "cross":
      return "M0,6 L6,0 M0,0 L6,6";
    case "dot":
      return "M3,3 m-1,0 a1,1 0 1,0 2,0 a1,1 0 1,0 -2,0";
    case "hline":
      return "M0,3 L6,3";
    case "vline":
      return "M3,0 L3,6";
    default:
      return "M0,6 L6,0";
  }
}

function luminance(color) {
  const c = d3.color(color);
  if (!c) return 0.5;
  return (0.3 * c.r + 0.59 * c.g + 0.11 * c.b) / 255;
}

function convertRemToPixels(rem) {
  return rem * parseFloat(getComputedStyle(document.documentElement).fontSize);
}

export default { render };
