import * as d3 from "d3";

async function render({ model,el}) {
  const fairData = model.get("fair_scores");
  const colorsData = model.get("source_colors");
  const grid = model.get("country_grid");

  let continer = document.createElement("div");
  continer.classList.add("cartogram");
  const body = d3.select(continer);

  el.appendChild(continer);

  renderFigure(body, grid, fairData, colorsData);
}


const renderFigure = (element, grid, data, colors) => {
  const width = 539;
  const height = 404.25;

  const svg = element
    .append("svg")
    .attr("xmlns", "http://www.w3.org/2000/svg")
    .attr("width", width)
    .attr("height", height);

  const scale = {
    F: d3
      .scaleOrdinal()
      .domain([...Array(colors.F.length + 1).keys()])
      .range([colors.empty].concat(colors.F)),
    A: d3
      .scaleOrdinal()
      .domain([...Array(colors.A.length + 1).keys()])
      .range([colors.empty].concat(colors.A)),
    I: d3
      .scaleOrdinal()
      .domain([...Array(colors.I.length + 1).keys()])
      .range([colors.empty].concat(colors.I)),
    R: d3
      .scaleOrdinal()
      .domain([...Array(colors.R.length + 1).keys()])
      .range([colors.empty].concat(colors.R)),
    TOTAL: d3
      .scaleLinear()
      .domain([0, 12])
      .range([colors.TOTAL[0], colors.TOTAL[2]]),
  };

  const marginLeftRight = 0;
  const margin = {
    top: 0,
    right: marginLeftRight,
    bottom: 0,
    left: marginLeftRight,
  };
  const separator = width * 0.04;
  const innerWidth = width * 0.365;
  const innerHeight = innerWidth;
  const widthSub = width * 0.28;

  const midSeparator = width * 0.6 - 2 * widthSub;
  const mainSeparator = height - 2 * innerWidth;
  const size = 10;
  const sizeSecondary = 7;
  const legendSize = 9;

  const rxMain = 5;
  const rxSub = 3;
  const textCorr = size * 0.4;

  const legendWidth = width - (separator + innerWidth);
  const legendHeight = height - (widthSub * 2 + midSeparator);

  svg
    .append("defs")
    .append("svg:clipPath")
    .attr("id", `clip-main`)
    .append("svg:rect")
    .attr("rx", rxMain)
    .attr("id", "clip-rect")
    .attr("x", -size)
    .attr("y", -size)
    .attr("width", size * 2)
    .attr("height", size * 2);

  const innerChart = svg
    .append("g")
    .attr("id", "main-figure")
    .attr("transform", `translate(${margin.left}, ${margin.top})`);

  renderLegend(
    scale,
    svg,
    innerWidth + separator + margin.left,
    2 * widthSub + midSeparator * 2,
    legendHeight,
    legendWidth,
    12,
    rxSub
  );
  renderFAIR(
    data,
    svg,
    margin.left,
    margin.top,
    size,
    innerHeight,
    innerWidth,
    scale,
    grid,
    textCorr
  );
  renderSub(
    margin.left,
    margin.top + innerHeight + mainSeparator,
    innerHeight,
    innerWidth,
    data,
    svg,
    size,
    scale,
    grid,
    rxMain,
    "TOTAL"
  );
  renderSub(
    innerWidth + separator + margin.left,
    margin.top,
    widthSub,
    widthSub,
    data,
    svg,
    sizeSecondary,
    scale,
    grid,
    rxSub,
    "F"
  );
  renderSub(
    innerWidth + separator + margin.left + midSeparator + widthSub,
    margin.top,
    widthSub,
    widthSub,
    data,
    svg,
    sizeSecondary,
    scale,
    grid,
    rxSub,
    "A"
  );
  renderSub(
    innerWidth + separator + margin.left,
    margin.top + midSeparator + widthSub,
    widthSub,
    widthSub,
    data,
    svg,
    sizeSecondary,
    scale,
    grid,
    rxSub,
    "I"
  );
  renderSub(
    innerWidth + separator + margin.left + midSeparator + widthSub,
    margin.top + midSeparator + widthSub,
    widthSub,
    widthSub,
    data,
    svg,
    sizeSecondary,
    scale,
    grid,
    rxSub,
    "R"
  );
};

const renderLegend = (legend, svg, x, y, height, width, size, rx) => {
  const legendElement = svg
    .append("g")
    .attr("id", "legend")
    .attr("transform", `translate(${x}, ${y})`);

  const innerScale = d3
    .scaleBand()
    .domain(["F", "A", "I", "R"])
    .range([0, width])
    .padding(0.0);

  const deepScale = d3
    .scaleBand()
    .domain([1, 2, 3])
    .range([0, innerScale.bandwidth() / 2]);
  const legendArray = [
    {
      letter: "F",
      text: "Findability",
      scale: legend.F,
    },
    { letter: "A", text: "Accessibility", scale: legend.A },
    { letter: "I", text: "Interoperability", scale: legend.I },
    { letter: "R", text: "Reusability", scale: legend.R },
  ];

  const total_values = [...Array(legend.TOTAL.domain()[1]).keys()].map(
    (a) => a + 1
  );
  const reference_colors = total_values.map((c) => legend.TOTAL(c));
  const lg_data = zipArrays(total_values, reference_colors);
  const totalScale = d3
    .scaleBand()
    .domain(total_values)
    .range([0, innerScale.bandwidth() * 2]);

  legendElement
    .append("text")
    .text("Total Score")
    .attr("y", size * 2.5)
    .attr("x", 0)
    .attr("dominant-baseline", "hanging")
    .attr("font-family", "Tinos, serif")
    .attr("font-weight", "500")
    .attr("font-size", size - 1)
    .attr("text-anchor", "start");

  legendElement
    .selectAll("rect")
    .data(lg_data)
    .join("rect")
    .attr("class", "legend-square")
    .attr("width", size)
    .attr("height", size)
    .attr("rx", rx)
    .attr("y", size * 3.5)
    .attr("x", (d) => totalScale(d[0]))
    .attr("fill", (d) => d[1]);

  legendElement
    .append("text")
    .text("No Score")
    .attr("y", size * 2.5)
    .attr("x", innerScale.bandwidth() * 3)
    .attr("dominant-baseline", "hanging")
    .attr("font-family", "Tinos, serif")
    .attr("font-weight", "500")
    .attr("font-size", size - 1)
    .attr("text-anchor", "start");

  legendElement
    .append("rect")
    .attr("class", "legend-square")
    .attr("width", size)
    .attr("height", size)
    .attr("rx", rx)
    .attr("y", size * 3.5)
    .attr("x", innerScale.bandwidth() * 3)
    .attr("fill", legend.F(0));

  legendElement
    .selectAll(".legend-item")
    .data(legendArray)
    .join((enter) => {
      const grp = enter
        .append("g")
        .attr("class", "legend-item")
        .attr(
          "transform",
          (d) => `translate(${innerScale(d.letter)}, 0)`
        );
      grp
        .append("text")
        .text((d) => d.text)
        .attr("y", 0)
        .attr("x", 0)
        .attr("dominant-baseline", "hanging")
        .attr("font-family", "Tinos, serif")
        .attr("font-weight", "500")
        .attr("font-size", size - 1)
        .attr("text-anchor", "start");

      grp
        .selectAll("rect")
        .data((d) => {
          const domain = d.scale.domain();
          const range = d.scale.range();
          return zipArrays(domain, range);
        })
        .join("rect")
        .attr("class", "legend-square")
        .attr("width", size)
        .attr("height", size)
        .attr("rx", rx)
        .attr("y", size)
        .attr("x", (d) => deepScale(d[0]))
        .attr("fill", (d) => d[1]);
    });
};

const renderFAIR = (
  data,
  svg,
  x,
  y,
  size,
  height,
  width,
  color,
  grid,
  text_correction
) => {
  const chart = svg.append("g").attr("transform", `translate(${x}, ${y})`);
  const arc = d3
    .arc()
    .outerRadius(size * 2)
    .innerRadius(0)
    .padAngle(0)
    .startAngle((d) => {
      return d.startAngle - Math.PI / 2;
    })
    .endAngle((d) => {
      return d.endAngle - Math.PI / 2;
    });

  const order_map = {
    F: 0,
    A: 1,
    I: 3,
    R: 2,
  };
  const fair_order = (a, b) => {
    return order_map[a[0]] - order_map[b[0]];
  };
  const sourceArray = data2Array(data, grid);
  const pie = d3
    .pie()
    .sort(fair_order)
    .value(function (d) {
      return d[1];
    });

  const sourcesPie = sourceArray.map((n) => {
    return {
      ...n,
      pie: pie(n.fair),
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
  chart
    .selectAll(".element")
    .data(sourcesPie)
    .join((enter) => {
      const grp = enter
        .append("g")
        .attr("class", "element")
        .attr(
          "transform",
          (d) =>
            `translate(${xPos(d.position[0])} ${yPos(d.position[1])})`
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
        .style("fill", function (d) {
          return color[d.data[0]](d.data[2]);
        });
      grp
        .append("text")
        .text((d) => d.country)
        .attr("dominant-baseline", "middle")
        .attr("font-family", "Tinos, serif")
        .attr("font-weight", "700")
        .attr("text-anchor", "middle")
        .attr("x", size)
        .attr("y", size + text_correction)
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
  rx,
  selection
) => {
  const innerChart = svg.append("g").attr("transform", `translate(${x}, ${y})`);

  const sourceArray = data2Array(data, grid);

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
          (d) =>
            `translate(${xPos(d.position[0])} ${yPos(d.position[1])})`
        );
      grp
        .append("rect")
        .attr("rx", rx)
        .attr("x", 0)
        .attr("y", 0)
        .attr("width", size * 2)
        .attr("height", size * 2)
        .attr(
          "fill",
          (d) => {
            let sel;
            if (selection == "TOTAL") {
              if (d.total == 0) {
                return color["F"](0);
              } else {
                sel = ["TOTAL", 0, d.total];
                return color[sel[0]](sel[2]);
              }
            } else {
              sel = d.fair.filter((s) => s[0] == selection)[0];
              return color[sel[0]](sel[2]);
            }
          }
        );
    });
};

const data2Array = (data, grid) => {
  const sourceArray = Object.keys(data).map((key) => {
    const fraction = 0.25;
    return {
      country: key,
      position: grid[key],
      fair: Object.keys(data[key])
        .map((d) => {
          if (d != "TOTAL") {
            return [d, fraction, data[key][d]];
          } else {
            return null;
          }
        })
        .filter((n) => n != null),
      total: data[key]["TOTAL"],
    };
  });
  return sourceArray;
};

function zipArrays(arr1, arr2) {
  return arr1.map((element, index) => [element, arr2[index]]);
}

export default { render };