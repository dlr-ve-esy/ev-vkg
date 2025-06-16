import * as d3 from "https://esm.sh/d3@7";

async function render({ model, el }) {
  const input = model.get("input");
  const width = model.get("width");
  const height = model.get("height");
  const barColor = model.get("bar_color");
  const customColors = model.get("custom_colors");
  const barRadius = model.get("bar_radius");
  const yTicks = model.get("y_ticks");
  const xTicks = model.get("x_ticks");
  var yMax = model.get("y_max");

  let continer = document.createElement("div");
  continer.classList.add("barchart");
  const body = d3.select(continer);
  console.log(input);
  el.appendChild(continer);

  renderBarChart(
    input,
    body,
    width,
    height,
    barColor,
    customColors,
    barRadius,
    yTicks,
    xTicks,
    yMax
  );
}

function renderBarChart(
  data,
  container,
  width = 500,
  height = 300,
  barColor = "steelblue",
  customColors = {},
  barRadius = 5,
  yTicks,
  xTicks,
  yMax
) {
  // Create SVG
  const svg = container
    .append("svg")
    .attr("width", width)
    .attr("height", height);

  // Margins and inner dimensions
  const margin = { top: 20, right: 20, bottom: 40, left: 40 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  // Create scales
  const xScale = d3
    .scaleBand()
    .domain(Object.keys(data)) // Use object keys for the x-axis
    .range([0, innerWidth])
    .padding(0.2);

  if (yMax === 0) {
    yMax = d3.max(Object.values(data));
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

  // Add y-axis gridlines
  chartGroup
    .append("g")
    .attr("class", "y-grid")
    .call(
      d3
        .axisLeft(yScale)
        .tickSize(-innerWidth) // Extend ticks across the width
        .tickFormat("") // Remove tick labels
    )
    .attr("stroke-opacity", 0.2); // Make gridlines lighter

  // Add clip-paths for rounded tops
  chartGroup
    .selectAll("clipPath")
    .data(Object.entries(data)) // Use object entries for data
    .join("clipPath")
    .attr("id", (d, i) => `clip-${i}`)
    .append("path")
    .attr("d", (d) => {
      const x = xScale(d[0]);
      const y = yScale(d[1]);
      const barWidth = xScale.bandwidth();
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

  // Add bars
  chartGroup
    .selectAll(".bar")
    .data(Object.entries(data)) // Use object entries for data
    .join("rect")
    .attr("class", "bar")
    .attr("x", (d) => xScale(d[0]))
    .attr("y", (d) => yScale(d[1]))
    .attr("width", xScale.bandwidth())
    .attr("height", (d) => innerHeight - yScale(d[1]))
    .attr("fill", (d) => customColors[d[0]] || barColor)
    .attr("clip-path", (d, i) => `url(#clip-${i})`);

  // Add x-axis with tick padding
  chartGroup
    .append("g")
    .attr("transform", `translate(0, ${innerHeight})`)
    .call(d3.axisBottom(xScale).tickSize(0).tickPadding(10)) // Add padding to x-axis ticks
    .selectAll("text")
    .style("text-anchor", "middle")
    .style("font-family", "Tinos, serif");

  const y_axis = d3.axisLeft(yScale).tickSize(0).tickPadding(10);
  if (yTicks.length > 0) {
    y_axis.tickValues(yTicks);
  }
  // Add y-axis with tick padding
  chartGroup.append("g").call(y_axis).style("font-family", "Tinos, serif"); // Add padding to y-axis ticks
}

export default { render };
