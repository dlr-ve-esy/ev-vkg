import * as d3 from "https://esm.sh/d3@7";

async function render({ model, el }) {
  const input = model.get("input");
  const colorC = model.get("color_col");
  const xAxis = model.get("x_axis");
  const yAxis = model.get("y_axis");
  const xDomain = model.get("x_domain");
  const yDomain = model.get("y_domain");
  const baseColor = model.get("base_color");
  const colors = model.get("colors");
  const width = model.get("width");
  const height = model.get("height");
  const margin = model.get("margin");
  const radius = model.get("radius");
  const celSize = model.get("cell_size");
  const xLabel = model.get("x_label");
  const yLabel = model.get("y_label");
  const fontSize = model.get("font_size");
  const xPadding = model.get("x_padding");
  const yPadding = model.get("y_padding");
  const yCorr = model.get("cell_ycorrection");

  let continer = document.createElement("div");
  continer.classList.add("scatter");

  const body = d3.select(continer);

  el.appendChild(continer);

  renderGrid(
    body,
    xDomain,
    yDomain,
    height,
    width,
    margin,
    input,
    celSize,
    baseColor,
    colors,
    radius,
    xLabel,
    yLabel,
    fontSize,
    xPadding,
    yPadding,
    colorC,
    xAxis,
    yAxis,
    yCorr
  );
}

const renderGrid = (
  container,
  xDomain,
  yDomain,
  height,
  width,
  margin,
  data,
  size,
  baseColor,
  colors,
  radius,
  xLabel,
  yLabel,
  fontSize,
  xPadding,
  yPadding,
  colorC = "code",
  xAxis = "x",
  yAxis = "y",
  yCorr = 0
) => {
  const svg = container
    .append("svg")
    .attr("width", width)
    .attr("height", height);

  const innerChart = svg
    .append("g")
    .attr("transform", `translate(${margin.left}, ${margin.top})`);

  // Margins and inner dimensions
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  const xValues = data.map((i) => i[xAxis]);
  const yValues = data.map((i) => i[yAxis]);
  console.log(yValues);
  console.log(xValues);
  const xPos = d3
    .scaleBand()
    .domain(xDomain)
    .range([0, innerWidth])
    .padding(xPadding);

  const yPos = d3
    .scaleBand()
    .domain(yDomain)
    .range([innerHeight, 0])
    .padding(yPadding);

  innerChart
    .selectAll(".element")
    .data(data)
    .join((enter) => {
      const grp = enter
        .append("g")
        .attr("class", "element")
        .attr("transform", (d) => {
          console.log(d);
          return `translate(${xPos(d[xAxis])} ${yPos(d[yAxis])})`;
        });
      grp
        .append("rect")
        .attr("x", 2)
        .attr("rx", radius)
        .attr("width", size)
        .attr("height", size)
        .attr("fill", (d) => colors[d[colorC]] || baseColor);

      grp
        .append("text")
        .text((d) => d[colorC])
        .attr("dominant-baseline", "middle")
        .attr("font-family", "Tinos, serif")
        .attr("font-weight", "700")
        .attr("text-anchor", "middle")
        .attr("x", size / 2 + 2)
        .attr("y", size / 2 + yCorr)
        .attr("font-size", `${fontSize * 1.3}rem`)
        .attr("fill", "white");
    });

  var x_axis = innerChart
    .append("g")
    .attr("id", "axisx")
    .attr("transform", `translate(0, ${innerHeight})`);

  x_axis.call(d3.axisBottom(xPos).tickSize(0));
  x_axis.selectAll("text").remove();

  var y_axis = innerChart.append("g").attr("id", "axisy");

  y_axis.call(d3.axisLeft(yPos).tickSize(0));
  y_axis.selectAll("text").remove();

  if (yLabel.length > 0) {
    innerChart
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
    innerChart
      .append("text")
      .attr("class", "label")
      .attr("text-anchor", "middle")
      .attr("y", innerHeight + 20)
      .attr("x", innerWidth / 2)
      .attr("opacity", 1)
      .style("font-family", "Tinos, serif")
      .attr("font-size", `${fontSize}rem`)
      .text(xLabel);
  }
};

export default { render };
