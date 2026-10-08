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

  const countries = Object.keys(data)
    .filter((c) => data[c]["TOTAL"] > 0)
    .sort((a, b) => data[b]["TOTAL"] - data[a]["TOTAL"]);

  const rowHeight = height / 2;

  renderStackedPlot(
    svg,
    data,
    countries,
    colors,
    0,
    0,
    width,
    rowHeight,
    barRadius,
    fontSize,
    "STACKED"
  );

  renderTotalPlot(
    svg,
    data,
    countries,
    colors,
    0,
    rowHeight,
    width,
    rowHeight,
    barRadius,
    fontSize,
    "TOTAL"
  );
};

const renderFrame = (svg, countries, x, y, width, height, fontSize, id) => {
  const margin = { top: 40, right: 10, bottom: 40, left: 35 };
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
  const yScale = d3.scaleLinear().domain([0, 12]).range([innerHeight, 0]);

  // Add y-axis gridlines
  const y_grid = d3
    .axisLeft(yScale)
    .tickSize(-innerWidth)
    .tickValues([3, 6, 9, 12])
    .tickFormat("");
  var axis = chart.append("g").attr("class", `y-grid-${id}`);
  axis.call(y_grid).attr("stroke-opacity", 0.2);
  axis.selectAll("path").style("opacity", 0);

  // Add x-axis with tick padding
  var x_axis = chart
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

  // Add y-axis with tick padding
  const y_axis = d3
    .axisLeft(yScale)
    .tickSize(0)
    .tickPadding(10)
    .tickValues([0, 3, 6, 9, 12]);
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

const renderStackedPlot = (
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
    id
  );

  renderTitle(chart, "Scores by principle", fontSize);
  renderLegend(chart, colors, innerWidth, fontSize, barRadius);

  const barWidth = xScale.bandwidth();

  countries.forEach((c, i) => {
    let cumulative = 0;
    const segments = PRINCIPLES.map((p) => {
      const value = data[c][p.key];
      const segment = { principle: p, value: value, base: cumulative };
      cumulative += value;
      return segment;
    }).filter((s) => s.value > 0);

    if (segments.length === 0) {
      return;
    }

    const total = cumulative;

    chart
      .append("clipPath")
      .attr("id", `clip-${id}-${i}`)
      .append("path")
      .attr("d", () =>
        roundedTopPath(
          xScale(c),
          yScale(total),
          barWidth,
          innerHeight - yScale(total),
          barRadius
        )
      );

    chart
      .selectAll(null)
      .data(segments)
      .join("rect")
      .attr("class", `segment-${id}-${i}`)
      .attr("x", xScale(c))
      .attr("y", (d) => yScale(d.base + d.value))
      .attr("width", barWidth)
      .attr("height", (d) => yScale(d.base) - yScale(d.base + d.value))
      .attr("fill", (d) => colors[d.principle.key][1])
      .attr("clip-path", `url(#clip-${id}-${i})`);
  });
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
    id
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

const renderLegend = (chart, colors, innerWidth, fontSize, barRadius) => {
  const size = convertRemToPixels(fontSize * 0.8);
  const spacing = size * 0.5;

  let offset = 0;
  const items = PRINCIPLES.map((p) => {
    const item = {
      principle: p,
      x: offset,
      width: size + spacing + p.title.length * size * 0.55,
    };
    offset += item.width + spacing * 3;
    return item;
  });
  const totalWidth = offset - spacing * 3;

  const legend = chart
    .append("g")
    .attr("class", "legend")
    .attr("transform", `translate(${innerWidth - totalWidth}, ${-14})`);

  items.forEach((item) => {
    const legendItem = legend
      .append("g")
      .attr("class", "legend-item")
      .attr("transform", `translate(${item.x}, 0)`);

    legendItem
      .append("rect")
      .attr("width", size)
      .attr("height", size)
      .attr("rx", barRadius / 2)
      .attr("ry", barRadius / 2)
      .attr("y", -size / 2)
      .attr("fill", colors[item.principle.key][1]);

    legendItem
      .append("text")
      .text(item.principle.title)
      .attr("x", size + spacing)
      .attr("y", size / 8)
      .attr("dominant-baseline", "middle")
      .style("font-family", "Tinos, serif")
      .attr("font-size", `${fontSize * 0.8}rem`);
  });
};

function convertRemToPixels(rem) {
  return rem * parseFloat(getComputedStyle(document.documentElement).fontSize);
}

export default { render };
