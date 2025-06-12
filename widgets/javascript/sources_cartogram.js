import * as d3 from "https://esm.sh/d3@7";

function render({ model, el }) {
  const sourceData = model.get("sources_per_country");
  const colorsData = model.get("source_colors");
  const legend = model.get("color_legend");
  const grid = model.get("country_grid");

  let continer = document.createElement("div");
  continer.classList.add("cartogram");
  const body = d3.select(continer);

  el.appendChild(continer);

  renderFigure(body, grid, sourceData, colorsData, legend);
}

const renderFigure = (element, grid, data, colors, legend) => {
  const width = 539;
  const height = 404.25;

  const svg = element
    .append("svg")
    .attr("xmlns", "http://www.w3.org/2000/svg")
    .attr("width", width)
    .attr("height", height);

  const color = d3
    .scaleOrdinal()
    .domain(Object.keys(colors))
    .range(Object.values(colors));

  const marginLeftRight = 0;
  const margin = {
    top: 1,
    right: marginLeftRight,
    bottom: 4,
    left: marginLeftRight,
  };
  const separator = width * 0.09;
  const innerWidth = width * 0.69;
  const innerHeight = innerWidth;
  const widthSub = width * 0.22;

  const midSeparator = (innerHeight - 3 * widthSub) / 2;

  const size = 18;
  const sizeSecondary = 6;
  const legendSize = 9;

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
    innerHeight + 3,
    20,
    width - width * 0.1,
    legendSize
  );
  renderMain(data, innerChart, size, innerHeight, innerWidth, color, grid);
  renderSub(
    innerWidth + separator + margin.left,
    margin.top,
    widthSub,
    widthSub,
    data,
    svg,
    sizeSecondary,
    color,
    grid,
    "Eco-Movement"
  );
  renderSub(
    innerWidth + separator + margin.left,
    margin.top + widthSub + midSeparator,
    widthSub,
    widthSub,
    data,
    svg,
    sizeSecondary,
    color,
    grid,
    "Tesla"
  );
  renderSub(
    innerWidth + separator + margin.left,
    margin.top + 2 * widthSub + 2 * midSeparator,
    widthSub,
    widthSub,
    data,
    svg,
    sizeSecondary,
    color,
    grid,
    "Chargemap"
  );
};

const renderLegend = (legend, svg, x, y, height, width, size) => {
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
        .attr("fill", (d) => d.color);

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

const renderMain = (data, chart, size, height, width, color, grid) => {
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
        .style("fill", (d) => color(d.data[0]));
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
        .attr("fill", "white");
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
  color,
  grid,
  selection
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
            ? color(selection)
            : "#b8b0ac"
        );
    });
};

export default { render };