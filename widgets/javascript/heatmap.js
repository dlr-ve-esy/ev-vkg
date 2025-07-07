import * as d3 from "https://esm.sh/d3@7";

async function render({ model, el }) {
  const input = model.get("input");
  const xAxis = model.get("x_axis");
  const yAxis = model.get("y_axis");
  const cAxis = model.get("c_axis");
  var cMax = model.get("c_max");
  var cMin = model.get("c_min");
  const width = model.get("width");
  const height = model.get("height");
  const margin = model.get("margin");
  const colors = model.get("colors");
  const baseColor = model.get("base_color");
  const radius = model.get("radius");
  const cellSize = model.get("cell_size");
  const xLabel = model.get("x_label");
  const yLabel = model.get("y_label");
  const xPadding = model.get("x_padding");
  const yPadding = model.get("y_padding");
  const fontSize = model.get("font_size");
  const invertC = model.get("invert_c");

  let continer = document.createElement("div");
  continer.classList.add("heatmap");
  const body = d3.select(continer);

  el.appendChild(continer);

  renderHeatMap(
    body,
    input,
    xAxis,
    yAxis,
    cAxis,
    width,
    height,
    margin,
    cMax,
    cMin,
    baseColor,
    colors,
    invertC,
    cellSize,
    radius,
    xPadding,
    yPadding,
    xLabel,
    yLabel,
    fontSize
  );
}

function renderHeatMap(
  container,
  input,
  xAxis,
  yAxis,
  cAxis,
  width,
  height,
  margin,
  cMax,
  cMin,
  baseColor,
  colors,
  invertC,
  cellSize,
  radius,
  xPadding,
  yPadding,
  xLabel,
  yLabel,
  fontSize
) {
  // Create SVG
  const svg = container
    .append("svg")
    .attr("width", width)
    .attr("height", height);

  // Margins and inner dimensions
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  // Create scales

  const xKeys = [...new Set(input.map((item) => item[xAxis]))];
  const yKeys = [...new Set(input.map((item) => item[yAxis]))];

  const xScale = d3
    .scaleBand()
    .domain(xKeys) // Use object keys for the x-axis
    .range([0, innerWidth])
    .padding(xPadding);

  const yScale = d3
    .scaleBand()
    .domain(yKeys)
    .range([innerHeight, 0])
    .padding(yPadding);

  const cValues = input.map((i) => i[cAxis]);

  if (!cMax) {
    cMax = d3.max(cValues);
  }

  if (!cMin) {
    cMin = d3.min(cValues);
  }
  var colorMaps = {};
  var cDomain;
  yKeys.forEach((key) => {
    const innercValues = input
      .filter((d) => d[yAxis] == key)
      .map((i) => i[cAxis]);
    if (colors[key]) {
      
      if (invertC) {
        cDomain = [colors[key], baseColor]
      } else {
        cDomain = [baseColor, colors[key]]
      }
      colorMaps[key] = d3
        .scaleLinear()
        .domain([d3.min(innercValues), d3.max(innercValues)])
        .range(cDomain)
        .interpolate(d3.interpolateLab);
    } else {
      // Default to black if the key is not in colors
      if (invertC) {
        cDomain = ["black", baseColor]
      } else {
        cDomain = [baseColor, "black"]
      }
      colorMaps[key] = d3
        .scaleLinear()
        .domain([d3.min(innercValues), d3.max(innercValues)])
        .range(cDomain)
        .interpolate(d3.interpolateLab);
    }
  });

  // Create chart group
  const chartGroup = svg
    .append("g")
    .attr("transform", `translate(${margin.left}, ${margin.top})`);

  // Draw stacks
  chartGroup
    .selectAll("rct")
    .data(input)
    .join("rect")
    .attr("class", "rct")
    .attr("fill", (d) => colorMaps[d[yAxis]](d[cAxis]) || "white")
    .attr("x", (d) => xScale(d[xAxis]) - cellSize / 2)
    .attr("y", (d) => yScale(d[yAxis]) - cellSize / 2)
    .attr("width", cellSize) // Ensure cells are square
    .attr("height", cellSize) // Ensure cells are square
    .attr("rx", radius)
    .attr("ry", radius);

  var x_axis = chartGroup
    .append("g")
    .attr("transform", `translate(0, ${innerHeight})`);

  x_axis
    .call(d3.axisBottom(xScale).tickSize(0))
    .selectAll("text")
    .attr("y", 0)
    .attr("x", -xScale.padding() - cellSize / 2)
    .style("text-anchor", "middle")
    .style("font-family", "Tinos, serif")
    .style("font-size", `${fontSize * 0.8}rem`)
    .style("opacity", 1);

  x_axis.selectAll("path").style("opacity", 0);
  var y_axis = chartGroup.append("g");

  y_axis
    .call(d3.axisLeft(yScale).tickSize(0))
    .selectAll("text")
    .attr("y", -cellSize / 2)
    .attr("x", -cellSize)
    .style("text-anchor", "end")
    .style("font-family", "Tinos, serif")
    .style("font-size", `${fontSize * 0.8}rem`)
    .style("opacity", 1);

  y_axis.selectAll("path").style("opacity", 0);
}

export default { render };
