import * as d3 from "https://esm.sh/d3@7";

async function render({ model, el }) {
  const input = model.get("input");
  const shadow = model.get("shadow");
  const markers = model.get("markers");
  const width = model.get("width");
  const height = model.get("height");
  const margin = model.get("margin");
  const barColor = model.get("bar_color");
  const markerColor = model.get("marker_color");
  const shadowColor = model.get("shadow_color");
  const customColors = model.get("custom_colors");
  const barRadius = model.get("bar_radius");
  const yTicks = model.get("y_ticks");
  const xTicks = model.get("x_ticks");
  const yGrid = model.get("y_grid");
  const xLabel = model.get("x_label");
  const yLabel = model.get("y_label");
  const Offset = model.get("offset");
  const fontSize = model.get("font_size");
  const mainLabel = model.get("main_label");
  const shadowLabel = model.get("shadow_label");
  const markerLabel = model.get("marker_label");
  var yMax = model.get("y_max");

  let continer = document.createElement("div");
  continer.classList.add("barchart");
  const body = d3.select(continer);
  console.log(input);
  el.appendChild(continer);

  renderBarChart(
    input,
    shadow,
    markers,
    body,
    width,
    height,
    margin,
    barColor,
    markerColor,
    shadowColor,
    customColors,
    barRadius,
    yTicks,
    xTicks,
    yGrid,
    xLabel,
    yLabel,
    yMax,
    Offset,
    fontSize,
    mainLabel,
    shadowLabel,
    markerLabel
  );
}

function renderBarChart(
  data,
  shadow,
  markers,
  container,
  width = 500,
  height = 300,
  margin,
  barColor = "steelblue",
  markerColor = "indianred",
  shadowColor = "black",
  customColors = {},
  barRadius = 5,
  yTicks,
  xTicks,
  yGrid,
  xLabel,
  yLabel,
  yMax,
  Offset,
  fontSize,
  mainLabel = "",
  shadowLabel = "",
  markerLabel = ""
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

  // Add clip-paths for shadow
  chartGroup
    .selectAll(".shadow-clip")
    .data(Object.entries(shadow)) // Use object entries for data
    .join("clipPath")
    .attr("class", "shadow-clip")
    .attr("id", (d, i) => `clip-shadow-${i}`)
    .append("path")
    .attr("d", (d) => {
      const x = xScale(d[0]) + xScale.bandwidth() * 0.1;
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

  // Add shadow bars
  chartGroup
    .selectAll(".shadow")
    .data(Object.entries(shadow))
    .join("rect")
    .attr("class", "shadow")
    .attr("x", (d) => xScale(d[0]) + xScale.bandwidth() * 0.1)
    .attr("y", (d) => yScale(d[1]))
    .attr("width", xScale.bandwidth())
    .attr("height", (d) => innerHeight - yScale(d[1]))
    .attr("fill", shadowColor)
    .attr("clip-path", (d, i) => `url(#clip-shadow-${i})`)
    .style("opacity", 0.6);

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

  // add markers
  chartGroup
    .selectAll(".marker")
    .data(Object.entries(markers))
    .join("line")
    .attr("class", "marker")
    .attr("x1", (d) => xScale(d[0]))
    .attr("y1", (d) => yScale(d[1]))
    .attr("x2", (d) => xScale(d[0]) + xScale.bandwidth() * 1.2)
    .attr("y2", (d) => yScale(d[1]))
    .attr("stroke", markerColor);

  function formatNumberWithCommas(number) {
    return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }
  const markerFornt = fontSize * 0.6666;
  chartGroup
    .selectAll(".marker-text")
    .data(Object.entries(markers))
    .join("text")
    .attr("class", "marker-text")
    .attr("x", (d) => xScale(d[0]) + xScale.bandwidth() * 1.2)
    .attr("y", (d) => yScale(d[1]))
    .attr("fill", markerColor)
    .attr("text-anchor", "end")
    .style("font-family", "Tinos, serif")
    .attr("font-size", `${markerFornt}rem`)
    .attr("dominant-baseline", "ideographic")
    .text((d) => formatNumberWithCommas(d[1]));

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
      .attr("y", innerHeight + Offset)
      .attr("x", innerWidth / 2)
      .attr("opacity", 0.6)
      .style("font-family", "Tinos, serif")
      .attr("font-size", `${fontSize}rem`)
      .text(xLabel);
  }

  if (mainLabel.length > 0 || shadowLabel.length > 0) {
    var legendArray = [];

    if (mainLabel.length > 0) {
      legendArray.push([mainLabel, barColor, 1]);
    }

    if (shadowLabel.length > 0) {
      legendArray.push([shadowLabel, shadowColor, 0.6]);
    }

    if (markerLabel.length > 0) {
      legendArray.push([markerLabel, markerColor, 1]);
    }
    const legendGroup = svg
      .append("g")
      .attr("class", "legend")
      .attr(
        "transform",
        `translate(${margin.left}, ${height - margin.bottom + Offset * 1.2})`
      );
    const legendSpacing = convertRemToPixels(fontSize * 0.8) * 0.5;
    const legendItemWidth = 10 * convertRemToPixels(fontSize * 0.8);
    const legendSquareSize = convertRemToPixels(fontSize * 0.8);

    legendGroup
      .selectAll(".legend-item")
      .data(legendArray)
      .join("g")
      .attr("class", "legend-item")
      .attr("transform", (d, i) => `translate(${i * legendItemWidth}, 0)`)
      .each(function (d) {
        const legendItem = d3.select(this);

        legendItem
          .append("rect")
          .attr("width", legendSquareSize)
          .attr("height", legendSquareSize)
          .attr("rx", barRadius / 2)
          .attr("ry", barRadius / 2)
          .attr("fill", d[1])
          .attr("y", -legendSquareSize / 2)
          .attr("opacity", d[2]);

        legendItem
          .append("text")
          .text(d[0])
          .attr("x", legendSquareSize + legendSpacing)
          .attr("y", legendSquareSize / 8)
          .attr("dominant-baseline", "middle")
          .style("font-family", "Tinos, serif")
          .attr("font-size", `${fontSize * 0.8}rem`)
          .style("opacity", 1);
      });
  }
}

function convertRemToPixels(rem) {
  return rem * parseFloat(getComputedStyle(document.documentElement).fontSize);
}
export default { render };
