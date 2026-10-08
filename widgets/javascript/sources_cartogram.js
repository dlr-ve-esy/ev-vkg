import * as d3 from "https://esm.sh/d3@7";

function render({ model, el }) {
  const sourceData = model.get("sources_per_country");
  const colorsData = model.get("source_colors");
  const legend = model.get("color_legend");
  const grid = model.get("country_grid");
  const width = model.get("width");
  const height = model.get("height");
  const size = model.get("marker_size");
  const sizeSecondary = model.get("marker_size_secondary");
  const legendSize = model.get("legend_marker_size");
  const legendHeight = model.get("legend_height");
  const sourceHatches = model.get("source_hatches");

  let continer = document.createElement("div");
  continer.classList.add("cartogram");
  const body = d3.select(continer);

  el.appendChild(continer);

  renderFigure(
    body,
    grid,
    sourceData,
    colorsData,
    legend,
    width,
    height,
    size,
    sizeSecondary,
    legendSize,
    legendHeight,
    sourceHatches
  );
}

const renderFigure = (
  element,
  grid,
  data,
  colors,
  legend,
  width = 539,
  height = 404,
  size = 18,
  sizeSecondary = 6,
  legendSize = 9,
  legendHeight = 20,
  sourceHatches = {}
) => {
  const svg = element
    .append("svg")
    .attr("xmlns", "http://www.w3.org/2000/svg")
    .attr("width", width)
    .attr("height", height);

  // Pattern per source category so categories sharing a fill
  // colour stay distinguishable.
  const fillOf = addHatchDefs(svg, sourceHatches, colors);

  const marginLeftRight = size;
  const margin = {
    top: size - 3,
    right: 0,
    bottom: 4,
    left: marginLeftRight,
  };
  const separator = width * 0.09;
  const innerWidth = width * 0.66;
  const innerHeight = innerWidth;
  const midSeparator = width * 0.015;
  const widthSub = (innerHeight - 2 * midSeparator) / 3;

  svg
    .append("defs")
    .append("svg:clipPath")
    .attr("id", `clip-main`)
    .append("svg:rect")
    .attr("rx", 5)
    .attr("id", "clip-rect")
    .attr("x", -size)
    .attr("y", -size)
    .attr("width", size * 2)
    .attr("height", size * 2);

  const innerChart = svg
    .append("g")
    .attr("id", "main-figure")
    .attr("transform", `translate(${margin.left}, ${margin.top})`);

  const legendArray = Object.keys(legend).map((key) => {
    return { source: key, color: legend[key] };
  });
  renderLegend(
    legendArray,
    svg,
    width * 0.05,
    innerHeight + margin.top,
    legendHeight,
    width - width * 0.1,
    legendSize,
    fillOf
  );
  renderMain(
    data,
    innerChart,
    size,
    innerHeight,
    innerWidth,
    grid,

    fillOf
  );
  renderSub(
    innerWidth + separator + margin.left,
    margin.top,
    widthSub,
    widthSub,
    data,
    svg,
    sizeSecondary,
    grid,

    "Eco-Movement",
    fillOf
  );
  renderSub(
    innerWidth + separator + margin.left,
    margin.top + widthSub + midSeparator,
    widthSub,
    widthSub,
    data,
    svg,
    sizeSecondary,
    grid,

    "Tesla",
    fillOf
  );
  renderSub(
    innerWidth + separator + margin.left,
    margin.top + 2 * widthSub + 2 * midSeparator,
    widthSub,
    widthSub,
    data,
    svg,
    sizeSecondary,
    grid,

    "Chargemap",
    fillOf
  );
};

const addHatchDefs = (svg, hatches, colors) => {
  // Returns a function mapping a source category to either its fill
  // colour or a pattern URL, based on the source_hatches mapping
  // (keyed by category, so categories can share a colour).
  const patterns = {};
  const defs = svg.append("defs");
  Object.entries(hatches).forEach(([source, hatch], i) => {
    if (hatch === "none" || hatch === undefined) {
      return;
    }
    const colorValue = colors[source];
    if (colorValue === undefined) {
      return;
    }
    const id = `source-hatch-${i}`;
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
    patterns[source] = `url(#${id})`;
  });
  return (source) => patterns[source] || colors[source] || "#b8b0ac";
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

const renderLegend = (legend, svg, x, y, height, width, size, fillOf) => {
  const band = d3
    .scaleBand()
    .domain(legend.map((d) => d.source))
    .range([0, width])
    .paddingInner(0);
  const pointpos = [...Array(legend.length).keys()].map(
    (l) => (l % 2) * height
  );
  const point = d3
    .scaleOrdinal()
    .domain(legend.map((d) => d.source))
    .range(pointpos);

  const legendElement = svg
    .append("g")
    .attr("id", "legend")
    .attr("transform", `translate(${x}, ${y})`);

  legendElement
    .selectAll(".legend-item")
    .data(legend)
    .join((enter) => {
      const grp = enter
        .append("g")
        .attr("class", "legend-item")
        .attr(
          "transform",
          (d) => `translate(${band(d.source)}, ${point(d.source)})`
        );
      grp
        .append("rect")
        .attr("width", size)
        .attr("rx", 2)
        .attr("height", size)
        .attr("fill", (d) => fillOf(d.source))
        .attr("stroke", "#4a4a4a")
        .attr("stroke-width", 0.4);

      grp
        .append("text")
        .text((d) => d.source)
        .attr("y", size / 2 + 0.75)
        .attr("x", size + 2)
        .attr("dominant-baseline", "middle")
        .attr("font-family", "Tinos, serif")
        .attr("font-weight", "500")
        .attr("font-size", size - 1)
        .attr("text-anchor", "left");
    });
};

const renderMain = (data, chart, size, height, width, grid, fillOf) => {
  const arc = d3
    .arc()
    .outerRadius(size * 2)
    .innerRadius(0)
    .padAngle(0)
    .startAngle((d) => d.startAngle + Math.PI / 4)
    .endAngle((d) => d.endAngle + Math.PI / 4);

  const sourceArray = Object.keys(data).map((key) => {
    const fraction = 1 / data[key].length;
    return {
      country: key,
      position: grid[key],
      sources: data[key].map((d) => [d, fraction]),
    };
  });
  const pie = d3
    .pie()
    .sort(null)
    .value((d) => d[1]);

  const sourcesPie = sourceArray.map((n) => ({
    ...n,
    pie: pie(n.sources),
  }));
  const xPos = d3
    .scaleBand()
    .domain([...Array(9).keys()])
    .range([0, width]);
  const yPos = d3
    .scaleBand()
    .domain([...Array(9).keys()])
    .range([0, height]);
  chart
    .selectAll(".element")
    .data(sourcesPie)
    .join((enter) => {
      const grp = enter
        .append("g")
        .attr("class", "element")
        .attr(
          "transform",
          (d) => `translate(${xPos(d.position[0])} ${yPos(d.position[1])})`
        );
      const pie = grp
        .selectAll(".pie")
        .data((d) => d.pie)
        .enter()
        .append("g")
        .attr("class", "pie")
        .attr("clip-path", `url(#clip-main)`)
        .attr("transform", `translate(${size},${size + 3})`);
      pie
        .append("path")
        .attr("d", arc)
        .style("fill", (d) => fillOf(d.data[0]));
      grp
        .append("text")
        .text((d) => d.country)
        .attr("dominant-baseline", "middle")
        .attr("font-family", "Tinos, serif")
        .attr("font-weight", "700")
        .attr("text-anchor", "middle")
        .attr("x", size)
        .attr("y", size * 1.3)
        .attr("font-size", size)
        .attr("fill", "white")
        .attr("stroke", "#262626")
        .attr("stroke-width", size * 0.14)
        .attr("stroke-linejoin", "round")
        .attr("paint-order", "stroke");
    });
};

const renderSub = (
  x,
  y,
  height,
  width,
  data,
  svg,
  size,
  grid,
  selection,
  fillOf
) => {
  const innerChart = svg.append("g").attr("transform", `translate(${x}, ${y})`);

  const sourceArray = Object.keys(data).map((key) => {
    const fraction = 1 / data[key].length;
    return {
      country: key,
      position: grid[key],
      sources: data[key].map((d) => [d, fraction]),
    };
  });

  const xPos = d3
    .scaleBand()
    .domain([...Array(9).keys()])
    .range([0, width]);
  const yPos = d3
    .scaleBand()
    .domain([...Array(9).keys()])
    .range([0, height]);

  innerChart
    .selectAll(".element")
    .data(sourceArray)
    .join((enter) => {
      const grp = enter
        .append("g")
        .attr("class", "element")
        .attr(
          "transform",
          (d) => `translate(${xPos(d.position[0])} ${yPos(d.position[1])})`
        );
      grp
        .append("rect")
        .attr("rx", 2)
        .attr("x", 0)
        .attr("y", 0)
        .attr("width", size * 2)
        .attr("height", size * 2)
        .attr("fill", (d) =>
          d.sources.map((s) => s[0]).includes(selection)
            ? fillOf(selection)
            : "#b8b0ac"
        );
    });
};

export default { render };
