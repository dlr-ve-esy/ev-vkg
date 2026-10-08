import * as d3 from "https://esm.sh/d3@7";

async function render({ model, el }) {
  const inputA = model.get("input_a");
  const inputB = model.get("input_b");
  const xKey = model.get("x_key");
  const width = model.get("width");
  const height = model.get("height");
  const catColors = model.get("cat_colors");
  const catHatches = model.get("cat_hatches");
  const barRadius = model.get("bar_radius");
  const yTicks = model.get("y_ticks");
  const xTicks = model.get("x_ticks");
  const yGrid = model.get("y_grid");
  const x1Label = model.get("x1_label");
  const x2Label = model.get("x2_label");
  const yLabel = model.get("y_label");
  const Offset = model.get("offset");
  const fontSize = model.get("font_size");
  const margin = model.get("margin");
  const legendItemWidth = model.get("legend_item_width");
  var yMax = model.get("y_max");

  let continer = document.createElement("div");
  continer.classList.add("barchart-double");
  const body = d3.select(continer);

  body.append("svg").attr("width", width).attr("height", height);

  el.appendChild(continer);
  const innerH = height * 0.475;
  const sep = height * 0.025;

  const marginTop = {
    top: margin.top,
    right: margin.right,
    bottom: Offset / 2 + 20,
    left: margin.left,
  };
  renderBarChartDouble(
    inputA,
    xKey,
    body,
    width,
    innerH,
    catColors,
    catHatches,
    barRadius,
    yTicks,
    xTicks,
    yGrid,
    x1Label,
    yLabel,
    yMax,
    Offset,
    false,
    fontSize,
    0,
    legendItemWidth,
    marginTop
  );

  const marginBottom = {
    top: 0,
    right: margin.right,
    bottom: margin.bottom,
    left: margin.left,
  };
  renderBarChartDouble(
    inputB,
    xKey,
    body,
    width,
    innerH,
    catColors,
    catHatches,
    barRadius,
    yTicks,
    xTicks,
    yGrid,
    x2Label,
    "",
    yMax,
    Offset,
    true,
    fontSize,
    innerH + sep,
    legendItemWidth,
    marginBottom
  );
}

function renderBarChartDouble(
  data,
  xKey,
  container,
  width = 500,
  height = 300,
  catColors = {},
  catHatches = {},
  barRadius = 5,
  yTicks,
  xTicks,
  yGrid,
  xLabel,
  yLabel,
  yMax,
  Offset,
  legend,
  fontSize,
  offsetY = 0,
  legendItemWidth = 10,
  margin = { top: 0, right: 20, bottom: 20, left: 70 }
) {
  console.log(data);
  const keys = Object.keys(data[0]).filter((k) => k !== xKey);
  const stack = d3.stack().keys(keys);
  const series = stack(data);

  const svg = container.select("svg");

  // Margins and inner dimensions

  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;

  // Create scales
  const xScale = d3
    .scaleBand()
    .domain(data.map((d) => d[xKey]))
    .range([0, innerWidth])
    .padding(0.2);

  if (!yMax || yMax === 0) {
    yMax = d3.max(series, (s) => d3.max(s, (d) => d[1]));
  }
  const yScale = d3
    .scaleLinear()
    .domain([0, yMax])
    .nice()
    .range([innerHeight, 0]);

  // Create chart group
  const chartGroup = svg
    .append("g")
    .attr("transform", `translate(${margin.left}, ${margin.top + offsetY})`);

  const y_grid = d3.axisLeft(yScale).tickSize(-innerWidth).tickFormat("");
  if (yGrid.length > 0) {
    y_grid.tickValues(yGrid);
  }

  // Add y-axis gridlines
  const axis = chartGroup.append("g").attr("class", "y-grid");
  axis.call(y_grid).attr("stroke-opacity", 0.2);
  axis.selectAll("path").style("opacity", 0);

  // Greyscale support: hatch pattern per band colour.
  const fillOf = addHatchDefs(svg, catHatches);

  // Add clip-paths for rounded tops
  chartGroup
    .selectAll("clipPath")
    .data(data.map((d) => d[xKey]))
    .join("clipPath")
    .attr("id", (d, i) => `clip-${d}-${offsetY}`) // Unique ID for each chart
    .append("path")
    .attr("d", (d, i) => {
      const x = xScale(d);
      const barWidth = xScale.bandwidth();
      const stackTops = series.map((s) => s[i][1]);
      const y = yScale(Math.max(...stackTops));
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

  // Draw stacks
  chartGroup
    .selectAll("g.stack")
    .data(series)
    .join("g")
    .attr("class", "stack")
    .attr("fill", (d) => fillOf(catColors[d.key] || "#888"))
    .selectAll("rect")
    .data((d) => d)
    .join("rect")
    .attr("x", (d, i) => xScale(data[i][xKey]))
    .attr("y", (d) => yScale(d[1]))
    .attr("height", (d) => yScale(d[0]) - yScale(d[1]))
    .attr("width", xScale.bandwidth())
    .attr("clip-path", (d, i) => `url(#clip-${data[i][xKey]}-${offsetY})`);

  // Add x-axis with tick padding
  const x_axis = chartGroup
    .append("g")
    .attr("transform", `translate(0, ${innerHeight})`);

  x_axis
    .call(d3.axisBottom(xScale).tickSize(0).tickPadding(10))
    .selectAll("text")
    .style("text-anchor", "middle")
    .style("font-family", "Tinos, serif")
    .style("font-size", `${fontSize * 0.8}rem`)
    .style("opacity", 1);

  x_axis.selectAll("path").style("opacity", 0.8);

  const y_axis = d3.axisLeft(yScale).tickSize(0).tickPadding(10);
  if (yTicks.length > 0) {
    y_axis.tickValues(yTicks);
  }

  // Add y-axis with tick padding
  const y_axis_ticks = chartGroup.append("g");
  y_axis_ticks
    .call(y_axis)
    .style("font-family", "Tinos, serif")
    .style("font-size", `${fontSize * 0.8}rem`)
    .style("opacity", 1);
  y_axis_ticks.selectAll("path").style("opacity", 0);

  // Add y label
  if (yLabel.length > 0) {
    chartGroup
      .append("text")
      .attr("class", "label")
      .attr("text-anchor", "start")
      .attr("y", -5)
      .attr("x", "0")
      .attr("opacity", 1)
      .style("font-family", "Tinos, serif")
      .attr("font-size", `${fontSize}rem`)
      .text(yLabel);
  }

  // Add x label
  if (xLabel.length > 0) {
    chartGroup
      .append("text")
      .attr("class", "label")
      .attr("text-anchor", "middle")
      .attr("y", innerHeight + Offset * 0.8)
      .attr("x", innerWidth / 2)
      .attr("opacity", 1)
      .style("font-family", "Tinos, serif")
      .attr("font-size", `${fontSize}rem`)
      .text(xLabel);
  }

  // Create legend items
  if (legend) {
    const legendGroup = svg
      .append("g")
      .attr("class", "legend")
      .attr(
        "transform",
        `translate(${margin.left}, ${
          height - margin.bottom + Offset * 1.2 + offsetY
        })`
      );

    const legendSpacing = convertRemToPixels(fontSize) * 0.2;
    const ItemWidth = legendItemWidth * convertRemToPixels(fontSize);
    const legendSquareSize = convertRemToPixels(fontSize);

    legendGroup
      .selectAll(".legend-item")
      .data(Object.entries(catColors))
      .join("g")
      .attr("class", "legend-item")
      .attr("transform", (d, i) => `translate(${i * ItemWidth}, 0)`)
      .each(function (d) {
        const legendItem = d3.select(this);

        legendItem
          .append("rect")
          .attr("width", legendSquareSize)
          .attr("height", legendSquareSize)
          .attr("rx", barRadius / 2)
          .attr("ry", barRadius / 2)
          .attr("fill", (d) => fillOf(d[1]))
          .attr("stroke", "#4a4a4a")
          .attr("stroke-width", 0.4)
          .attr("y", -legendSquareSize / 2);

        legendItem
          .append("text")
          .text(d[0])
          .attr("x", legendSquareSize + legendSpacing)
          .attr("y", legendSquareSize / 8)
          .attr("dominant-baseline", "middle")
          .style("font-family", "Tinos, serif")
          .attr("font-size", `${fontSize}rem`)
          .style("opacity", 1);
      });
  }
}
const addHatchDefs = (svg, hatches) => {
  const patterns = {};
  const defs = svg.append("defs");
  Object.entries(hatches).forEach(([colorValue, hatch], i) => {
    if (hatch === "none" || hatch === undefined) {
      return;
    }
    const id = `band-hatch-${i}`;
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
      .attr("fill", colorValue);
    const c = d3.color(colorValue);
    const lum = (0.3 * c.r + 0.59 * c.g + 0.11 * c.b) / 255;
    const line = lum > 0.55 ? "#4a4a4a" : "#ffffff";
    pattern
      .append("path")
      .attr("d", hatchPath(hatch))
      .attr("stroke", line)
      .attr("stroke-width", 1.1)
      .attr("fill", "none");
    patterns[colorValue] = `url(#${id})`;
  });
  return (colorValue) => patterns[colorValue] || colorValue;
};

const hatchPath = (hatch) => {
  switch (hatch) {
    case "diag":
      return "M0,6 L6,0";
    case "diag2":
      return "M0,0 L6,6";
    case "cross":
      return "M0,6 L6,0 M0,0 L6,6";
    case "grid":
      return "M0,3 L6,3 M3,0 L3,6";
    case "dot":
      return "M3,3 m-1,0 a1,1 0 1,0 2,0 a1,1 0 1,0 -2,0";
    case "hline":
      return "M0,3 L6,3";
    case "vline":
      return "M3,0 L3,6";
    default:
      return "M0,6 L6,0";
  }
};

function convertRemToPixels(rem) {
  return rem * parseFloat(getComputedStyle(document.documentElement).fontSize);
}
export default { render };
