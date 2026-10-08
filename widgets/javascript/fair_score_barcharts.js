import * as d3 from "https://esm.sh/d3@7";

async function render({ model, el }) {
  const fairData = model.get("fair_scores");
  const colorsData = model.get("source_colors");
  const width = model.get("width");
  const height = model.get("height");
  const barRadius = model.get("bar_radius");
  const fontSize = model.get("font_size");

  let continer = document.createElement("div");
  continer.classList.add("fair-barcharts");
  const body = d3.select(continer);

  el.appendChild(continer);

  renderFigure(body, fairData, colorsData, width, height, barRadius, fontSize);
}

const PRINCIPLES = [
  { key: "F", title: "Findability" },
  { key: "A", title: "Accessibility" },
  { key: "I", title: "Interoperability" },
  { key: "R", title: "Reusability" },
];

const renderFigure = (
  element,
  data,
  colors,
  width = 700,
  height = 640,
  barRadius = 4,
  fontSize = 0.8
) => {
  const svg = element
    .append("svg")
    .attr("xmlns", "http://www.w3.org/2000/svg")
    .attr("width", width)
    .attr("height", height);

  // Shared country list for every plot: drop only TOTAL == 0 countries,
  // order by total score descending (ties by country code) so all x axes match.
  const countries = Object.keys(data)
    .filter((c) => data[c]["TOTAL"] > 0)
    .sort(
      (a, b) => data[b]["TOTAL"] - data[a]["TOTAL"] || a.localeCompare(b)
    );

  const gap = 4;
  const bottomHeight = Math.round(height * 0.32);
  const topHeight = height - bottomHeight - gap;
  const cellWidth = (width - gap) / 2;
  const cellHeight = (topHeight - gap) / 2;

  PRINCIPLES.forEach((p, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    renderPrinciplePlot(
      svg,
      data,
      countries,
      colors,
      p,
      col * (cellWidth + gap),
      row * (cellHeight + gap),
      cellWidth,
      cellHeight,
      barRadius,
      fontSize,
      p.key,
      row === 1
    );
  });

  renderTotalPlot(
    svg,
    data,
    countries,
    colors,
    0,
    topHeight + gap,
    width,
    bottomHeight,
    barRadius,
    fontSize,
    "TOTAL"
  );
};

const renderFrame = (
  svg,
  countries,
  x,
  y,
  width,
  height,
  fontSize,
  id,
  yMax,
  yTicks,
  showXLabels,
  xLabelFactor
) => {
  const margin = {
    top: 32,
    right: 10,
    bottom: showXLabels ? 40 : 12,
    left: 35,
  };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;

  const chart = svg
    .append("g")
    .attr("transform", `translate(${x + margin.left}, ${y + margin.top})`);

  const xScale = d3
    .scaleBand()
    .domain(countries)
    .range([0, innerWidth])
    .padding(0.2);
  const yScale = d3.scaleLinear().domain([0, yMax]).range([innerHeight, 0]);

  // Add y-axis gridlines
  const y_grid = d3
    .axisLeft(yScale)
    .tickSize(-innerWidth)
    .tickValues(yTicks)
    .tickFormat("");
  var axis = chart.append("g").attr("class", `y-grid-${id}`);
  axis.call(y_grid).attr("stroke-opacity", 0.2);
  axis.selectAll("path").style("opacity", 0);

  // Add x-axis with tick padding
  var x_axis = chart
    .append("g")
    .attr("transform", `translate(0, ${innerHeight})`);

  x_axis
    .call(
      d3
        .axisBottom(xScale)
        .tickSize(0)
        .tickPadding(10)
        .tickFormat(showXLabels ? null : "")
    )
    .selectAll("text")
    .style("text-anchor", "middle")
    .style("font-family", "Tinos, serif")
    .style("font-size", `${fontSize * xLabelFactor}rem`)
    .style("opacity", 1);

  x_axis.selectAll("path").style("opacity", 0.8);

  // Add y-axis with tick padding
  const y_axis = d3
    .axisLeft(yScale)
    .tickSize(0)
    .tickPadding(10)
    .tickValues([0, ...yTicks]);
  var y_axis_ticks = chart.append("g");

  y_axis_ticks
    .call(y_axis)
    .style("font-family", "Tinos, serif")
    .style("font-size", `${fontSize * 0.8}rem`)
    .style("opacity", 1);
  y_axis_ticks.selectAll("path").style("opacity", 0);

  return { chart, xScale, yScale, innerWidth, innerHeight };
};

const renderTitle = (chart, text, fontSize) => {
  chart
    .append("text")
    .attr("class", "title")
    .text(text)
    .attr("x", 0)
    .attr("y", -14)
    .attr("font-family", "Tinos, serif")
    .attr("font-weight", "500")
    .attr("font-size", `${fontSize}rem`)
    .attr("text-anchor", "start");
};

const roundedTopPath = (bx, by, barWidth, barHeight, barRadius) => `
  M${bx},${by + barRadius} 
  Q${bx},${by} ${bx + barRadius},${by} 
  L${bx + barWidth - barRadius},${by} 
  Q${bx + barWidth},${by} ${bx + barWidth},${by + barRadius} 
  L${bx + barWidth},${by + barHeight} 
  L${bx},${by + barHeight} 
  Z
`;

const renderPrinciplePlot = (
  svg,
  data,
  countries,
  colors,
  principle,
  x,
  y,
  width,
  height,
  barRadius,
  fontSize,
  id,
  showXLabels
) => {
  const { chart, xScale, yScale, innerWidth, innerHeight } = renderFrame(
    svg,
    countries,
    x,
    y,
    width,
    height,
    fontSize,
    id,
    3,
    [1, 2, 3],
    showXLabels,
    0.6
  );

  renderTitle(chart, principle.title, fontSize);

  const barWidth = xScale.bandwidth();

  // Add clip-paths for rounded tops
  chart
    .selectAll("clipPath")
    .data(countries)
    .join("clipPath")
    .attr("id", (d, i) => `clip-${id}-${i}`)
    .append("path")
    .attr("d", (d) =>
      roundedTopPath(
        xScale(d),
        yScale(data[d][principle.key]),
        barWidth,
        innerHeight - yScale(data[d][principle.key]),
        barRadius
      )
    );

  // Add bars; zero-score countries keep a zero-height bar so the
  // shared x axis stays intact across all plots.
  chart
    .selectAll(".bar")
    .data(countries)
    .join("rect")
    .attr("class", "bar")
    .attr("x", (d) => xScale(d))
    .attr("y", (d) => yScale(data[d][principle.key]))
    .attr("width", barWidth)
    .attr("height", (d) => innerHeight - yScale(data[d][principle.key]))
    .attr("fill", colors[principle.key][1])
    .attr("clip-path", (d, i) => `url(#clip-${id}-${i})`);
};

const renderTotalPlot = (
  svg,
  data,
  countries,
  colors,
  x,
  y,
  width,
  height,
  barRadius,
  fontSize,
  id
) => {
  const { chart, xScale, yScale, innerWidth, innerHeight } = renderFrame(
    svg,
    countries,
    x,
    y,
    width,
    height,
    fontSize,
    id,
    12,
    [3, 6, 9, 12],
    true,
    0.8
  );

  renderTitle(chart, "Total Score", fontSize);

  const totalScale = d3
    .scaleLinear()
    .domain([0, 12])
    .range([colors.TOTAL[0], colors.TOTAL[2]]);

  const barWidth = xScale.bandwidth();

  // Add clip-paths for rounded tops
  chart
    .selectAll("clipPath")
    .data(countries)
    .join("clipPath")
    .attr("id", (d, i) => `clip-${id}-${i}`)
    .append("path")
    .attr("d", (d) =>
      roundedTopPath(
        xScale(d),
        yScale(data[d]["TOTAL"]),
        barWidth,
        innerHeight - yScale(data[d]["TOTAL"]),
        barRadius
      )
    );

  // Add bars
  chart
    .selectAll(".bar")
    .data(countries)
    .join("rect")
    .attr("class", "bar")
    .attr("x", (d) => xScale(d))
    .attr("y", (d) => yScale(data[d]["TOTAL"]))
    .attr("width", barWidth)
    .attr("height", (d) => innerHeight - yScale(data[d]["TOTAL"]))
    .attr("fill", (d) =>
      data[d]["TOTAL"] === 0 ? colors.empty : totalScale(data[d]["TOTAL"])
    )
    .attr("clip-path", (d, i) => `url(#clip-${id}-${i})`);
};

export default { render };
