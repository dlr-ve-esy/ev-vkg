import * as d3 from "https://esm.sh/d3@7";

async function render({ model, el }) {
  const input = model.get("input");
  const xKey = model.get("x_key");
  const width = model.get("width");
  const height = model.get("height");
  const catColors = model.get("cat_colors");
  const barRadius = model.get("bar_radius");
  const yTicks = model.get("y_ticks");
  const xTicks = model.get("x_ticks");
  const yGrid = model.get("y_grid");
  const xLabel = model.get("x_label");
  const yLabel = model.get("y_label");
  const Offset = model.get("offset");
  const legend = model.get("legend");
  const fontSize = model.get("font_size");
  var yMax = model.get("y_max");

  let continer = document.createElement("div");
  continer.classList.add("barchart");
  const body = d3.select(continer);
  el.appendChild(continer);

  renderBarChart(
    input,
    xKey,
    body,
    width,
    height,
    catColors,
    barRadius,
    yTicks,
    xTicks,
    yGrid,
    xLabel,
    yLabel,
    yMax,
    Offset,
    legend,
    fontSize
  );
}

function renderBarChart(
  data,
  xKey,
  container,
  width = 500,
  height = 300,
  catColors = {},
  barRadius = 5,
  yTicks,
  xTicks,
  yGrid,
  xLabel,
  yLabel,
  yMax,
  Offset,
  legend,
  fontSize
) {
  const keys = Object.keys(data[0]).filter((k) => k !== xKey);
  // Stack the data
  const stack = d3.stack().keys(keys);
  const series = stack(data);
  // Create SVG
  const svg = container
    .append("svg")
    .attr("width", width)
    .attr("height", height);

  // Margins and inner dimensions
  const margin = { top: 20, right: 20, bottom: 40, left: 50 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  // Create scales
  const xScale = d3
    .scaleBand()
    .domain(data.map((d) => d[xKey])) // Use object keys for the x-axis
    .range([0, innerWidth])
    .padding(0.2);

  if (!yMax || yMax === 0) {
    yMax = d3.max(series, (s) => d3.max(s, (d) => d[1]));
  }
  const yScale = d3
    .scaleLinear()
    .domain([0, yMax]) // Use object values for the y-axis
    .nice()
    .range([innerHeight, 0]);

  // Create chart group
  const chartGroup = svg
    .append("g")
    .attr("transform", `translate(${margin.left}, ${margin.top})`);

  const y_grid = d3.axisLeft(yScale).tickSize(-innerWidth).tickFormat("");
  if (yGrid.length > 0) {
    y_grid.tickValues(yGrid);
  }

  // Add y-axis gridlines
  var axis = chartGroup.append("g").attr("class", "y-grid");
  axis.call(y_grid).attr("stroke-opacity", 0.2);
  axis.selectAll("path").style("opacity", 0);

  // Add clip-paths for rounded tops
  chartGroup
    .selectAll("clipPath")
    .data(data.map((d) => d[xKey])) // Use object entries for data
    .join("clipPath")
    .attr("id", (d, i) => `clip-${d}`)
    .append("path")
    .attr("d", (d, i) => {
      const x = xScale(d);
      const barWidth = xScale.bandwidth();
      // Find the top of the stack (the minimum y of all stacks at this x)
      console.log(series);
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
    .attr("fill", (d) => catColors[d.key] || "#888")
    .selectAll("rect")
    .data((d) => d)
    .join("rect")
    .attr("x", (d, i) => xScale(data[i][xKey]))
    .attr("y", (d) => yScale(d[1]))
    .attr("height", (d) => yScale(d[0]) - yScale(d[1]))
    .attr("width", xScale.bandwidth())
    .attr("clip-path", (d, i) => `url(#clip-${data[i][xKey]})`);

  // Add x-axis with tick padding
  var x_axis = chartGroup
    .append("g")
    .attr("transform", `translate(0, ${innerHeight})`);

  x_axis
    .call(d3.axisBottom(xScale).tickSize(0).tickPadding(10)) // Add padding to x-axis ticks
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
  var y_axis_ticks = chartGroup.append("g");

  y_axis_ticks
    .call(y_axis)
    .style("font-family", "Tinos, serif")
    .style("font-size", `${fontSize * 0.8}rem`)
    .style("opacity", 1); // Add padding to y-axis ticks
  y_axis_ticks.selectAll("path").style("opacity", 0);

  // Add y label
  if (yLabel.length > 0) {
    chartGroup
      .append("text")
      .attr("class", "label")
      .attr("text-anchor", "start")
      .attr("y", "-0.5em")
      .attr("x", "0")
      .attr("opacity", 1)
      .attr("font-family", "Tinos, serif")
      .attr("font-size", `${fontSize}rem`)
      .text(yLabel);
  }
  // Add x label
  if (xLabel.length > 0) {
    chartGroup
      .append("text")
      .attr("class", "label")
      .attr("text-anchor", "middle")
      .attr("y", innerHeight + Offset)
      .attr("x", innerWidth / 2)
      .attr("opacity", 1)
      .style("font-family", "Tinos, serif")
      .attr("font-size", `${fontSize}rem`)
      .text(xLabel);
  }

  // Create legend items
  if (legend) {
    // Add legend below the plot
    const legendGroup = svg
      .append("g")
      .attr("class", "legend")
      .attr(
        "transform",
        `translate(${margin.left}, ${height - margin.bottom + Offset})`
      );

    const legendSpacing = convertRemToPixels(fontSize) * 0.5;
    const legendItemWidth = 10 * convertRemToPixels(fontSize);
    const legendSquareSize = convertRemToPixels(fontSize);

    legendGroup
      .selectAll(".legend-item")
      .data(Object.entries(catColors))
      .join("g")
      .attr("class", "legend-item")
      .attr(
        "transform",
        (d, i) => `translate(${i * legendItemWidth}, 0)` // Position each legend item
      )
      .each(function (d) {
        const legendItem = d3.select(this);

        // Add color square
        legendItem
          .append("rect")
          .attr("width", legendSquareSize)
          .attr("height", legendSquareSize)
          .attr("rx", barRadius / 2)
          .attr("ry", barRadius / 2)
          .attr("fill", d[1]) // Use the color from catColors
          .attr("y", -legendSquareSize / 2);

        // Add label
        legendItem
          .append("text")
          .text(d[0]) // Use the key as the label
          .attr("x", legendSquareSize + legendSpacing)
          .attr("y", legendSquareSize / 8)
          .attr("dominant-baseline", "middle")
          .style("font-family", "Tinos, serif")
          .style("font-size", `${fontSize}rem`)
          .style("opacity", 1);
      });
  }
}
function convertRemToPixels(rem) {
  return rem * parseFloat(getComputedStyle(document.documentElement).fontSize);
}
export default { render };
