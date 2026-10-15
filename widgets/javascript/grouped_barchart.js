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
  const barRadius = model.get("bar_radius");
  const yTicks = model.get("y_ticks");
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
  el.appendChild(continer);
  const body = d3.select(continer);

  renderGroupedBarChart(
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
    barRadius,
    yTicks,
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

function renderGroupedBarChart(
  data,
  shadow,
  markers,
  container,
  width = 500,
  height = 300,
  margin,
  barColor = "#4d4d4d",
  markerColor = "#1a1a1a",
  shadowColor = "#c9c9c9",
  barRadius = 4,
  yTicks,
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
  const svg = container.append("svg").attr("width", width).attr("height", height);

  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;

  const codes = Object.keys(data);
  const xScale = d3
    .scaleBand()
    .domain(codes)
    .range([0, innerWidth])
    .padding(0.2);

  if (!yMax || yMax === 0) {
    yMax = d3.max(Object.values(data));
  }
  const yScale = d3
    .scaleLinear()
    .domain([0, yMax])
    .nice()
    .range([innerHeight, 0]);

  const chartGroup = svg
    .append("g")
    .attr("transform", `translate(${margin.left}, ${margin.top})`);

  // Greyscale-safe series fills: the calculated series solid dark, the
  // EAFO reference light with a diagonal hatch.
  const shadowFill = addHatchFill(svg, "grouped-shadow", shadowColor, "diag");

  const y_grid = d3.axisLeft(yScale).tickSize(-innerWidth).tickFormat("");
  if (yGrid.length > 0) {
    y_grid.tickValues(yGrid);
  }
  const axis = chartGroup.append("g").attr("class", "y-grid");
  axis.call(y_grid).attr("stroke-opacity", 0.2);
  axis.selectAll("path").style("opacity", 0);

  // Two side-by-side bars per country.
  const barWidth = xScale.bandwidth() * 0.4;
  const xMain = (code) => xScale(code) + xScale.bandwidth() * 0.06;
  const xShadow = (code) => xScale(code) + xScale.bandwidth() * 0.54;

  // Rounded-top clip paths for both series.
  const clipData = [];
  codes.forEach((code) => {
    clipData.push({ id: `clip-main-${code}`, x: xMain(code), value: data[code] });
    if (shadow[code] !== null && shadow[code] !== undefined) {
      clipData.push({
        id: `clip-shadow-${code}`,
        x: xShadow(code),
        value: shadow[code],
      });
    }
  });
  chartGroup
    .selectAll("clipPath")
    .data(clipData)
    .join("clipPath")
    .attr("id", (d) => d.id)
    .append("path")
    .attr("d", (d) => {
      const y = yScale(d.value);
      const barHeight = innerHeight - y;
      return `
        M${d.x},${y + barRadius}
        Q${d.x},${y} ${d.x + barRadius},${y}
        L${d.x + barWidth - barRadius},${y}
        Q${d.x + barWidth},${y} ${d.x + barWidth},${y + barRadius}
        L${d.x + barWidth},${y + barHeight}
        L${d.x},${y + barHeight}
        Z
      `;
    });

  // EAFO reference bars (skipped where no reference exists, e.g. IS/NO).
  chartGroup
    .selectAll(".shadow")
    .data(codes.filter((c) => shadow[c] !== null && shadow[c] !== undefined))
    .join("rect")
    .attr("class", "shadow")
    .attr("x", (d) => xShadow(d))
    .attr("y", (d) => yScale(shadow[d]))
    .attr("width", barWidth)
    .attr("height", (d) => innerHeight - yScale(shadow[d]))
    .attr("fill", shadowFill)
    .attr("stroke", "#8a8a8a")
    .attr("stroke-width", 0.5)
    .attr("clip-path", (d) => `url(#clip-shadow-${d})`);

  // Calculated bars.
  chartGroup
    .selectAll(".bar")
    .data(codes)
    .join("rect")
    .attr("class", "bar")
    .attr("x", (d) => xMain(d))
    .attr("y", (d) => yScale(data[d]))
    .attr("width", barWidth)
    .attr("height", (d) => innerHeight - yScale(data[d]))
    .attr("fill", barColor)
    .attr("clip-path", (d) => `url(#clip-main-${d})`);

  // AFIR target markers spanning the full country group.
  chartGroup
    .selectAll(".marker")
    .data(Object.entries(markers))
    .join("line")
    .attr("class", "marker")
    .attr("x1", (d) => xScale(d[0]))
    .attr("y1", (d) => yScale(d[1]))
    .attr("x2", (d) => xScale(d[0]) + xScale.bandwidth())
    .attr("y2", (d) => yScale(d[1]))
    .attr("stroke", markerColor)
    .attr("stroke-width", 1.2);

  function formatNumberWithCommas(number) {
    return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }
  const markerFont = fontSize * 0.6666;
  chartGroup
    .selectAll(".marker-text")
    .data(Object.entries(markers))
    .join("text")
    .attr("class", "marker-text")
    .attr("x", (d) => xScale(d[0]) + xScale.bandwidth())
    .attr("y", (d) => yScale(d[1]))
    .attr("fill", markerColor)
    .attr("text-anchor", "end")
    .style("font-family", "Tinos, serif")
    .attr("font-size", `${markerFont}rem`)
    .attr("dominant-baseline", "ideographic")
    .text((d) => formatNumberWithCommas(d[1]));

  // X axis.
  const x_axis = chartGroup
    .append("g")
    .attr("transform", `translate(0, ${innerHeight})`);
  x_axis
    .call(d3.axisBottom(xScale).tickSize(0).tickPadding(10))
    .selectAll("text")
    .style("text-anchor", "middle")
    .style("font-family", "Tinos, serif")
    .style("font-size", `${fontSize * 0.8}rem`);
  x_axis.selectAll("path").style("opacity", 0.8);

  // Y axis.
  const y_axis = d3.axisLeft(yScale).tickSize(0).tickPadding(10);
  if (yTicks.length > 0) {
    y_axis.tickValues(yTicks);
  }
  const y_axis_ticks = chartGroup.append("g");
  y_axis_ticks
    .call(y_axis)
    .style("font-family", "Tinos, serif")
    .style("font-size", `${fontSize * 0.8}rem`);
  y_axis_ticks.selectAll("path").style("opacity", 0);

  if (yLabel.length > 0) {
    chartGroup
      .append("text")
      .attr("text-anchor", "start")
      .attr("y", -5)
      .attr("x", 0)
      .style("font-family", "Tinos, serif")
      .attr("font-size", `${fontSize}rem`)
      .text(yLabel);
  }
  if (xLabel.length > 0) {
    chartGroup
      .append("text")
      .attr("text-anchor", "middle")
      .attr("y", innerHeight + Offset)
      .attr("x", innerWidth / 2)
      .attr("opacity", 0.6)
      .style("font-family", "Tinos, serif")
      .attr("font-size", `${fontSize}rem`)
      .text(xLabel);
  }

  // Legend.
  if (mainLabel.length > 0 || shadowLabel.length > 0 || markerLabel.length > 0) {
    const legendGroup = svg
      .append("g")
      .attr("class", "legend")
      .attr(
        "transform",
        `translate(${margin.left}, ${height - margin.bottom + Offset * 1.2})`
      );
    const legendSpacing = convertRemToPixels(fontSize * 0.8) * 0.5;
    const legendItemWidth = 11 * convertRemToPixels(fontSize * 0.8);
    const legendSquareSize = convertRemToPixels(fontSize * 0.8);

    const items = [];
    if (mainLabel.length > 0) {
      items.push({ label: mainLabel, type: "rect", fill: barColor });
    }
    if (shadowLabel.length > 0) {
      items.push({ label: shadowLabel, type: "rect", fill: shadowFill });
    }
    if (markerLabel.length > 0) {
      items.push({ label: markerLabel, type: "line", fill: markerColor });
    }

    legendGroup
      .selectAll(".legend-item")
      .data(items)
      .join("g")
      .attr("class", "legend-item")
      .attr("transform", (d, i) => `translate(${i * legendItemWidth}, 0)`)
      .each(function (d) {
        const legendItem = d3.select(this);
        if (d.type === "rect") {
          legendItem
            .append("rect")
            .attr("width", legendSquareSize)
            .attr("height", legendSquareSize)
            .attr("rx", barRadius / 2)
            .attr("ry", barRadius / 2)
            .attr("fill", d.fill)
            .attr("stroke", "#8a8a8a")
            .attr("stroke-width", 0.5)
            .attr("y", -legendSquareSize / 2);
        } else {
          legendItem
            .append("line")
            .attr("x1", 0)
            .attr("y1", 0)
            .attr("x2", legendSquareSize)
            .attr("y2", 0)
            .attr("stroke", d.fill)
            .attr("stroke-width", 1.2);
        }
        legendItem
          .append("text")
          .text(d.label)
          .attr("x", legendSquareSize + legendSpacing)
          .attr("y", legendSquareSize / 8)
          .attr("dominant-baseline", "middle")
          .style("font-family", "Tinos, serif")
          .attr("font-size", `${fontSize * 0.8}rem`);
      });
  }
}

function addHatchFill(svg, id, color, hatch) {
  const defs = svg.select("defs").empty()
    ? svg.append("defs")
    : svg.select("defs");
  const pattern = defs
    .append("pattern")
    .attr("id", `hatch-${id}`)
    .attr("width", 6)
    .attr("height", 6)
    .attr("patternUnits", "userSpaceOnUse");
  pattern.append("rect").attr("width", 6).attr("height", 6).attr("fill", color);
  const c = d3.color(color);
  const lum = (0.3 * c.r + 0.59 * c.g + 0.11 * c.b) / 255;
  pattern
    .append("path")
    .attr("d", "M0,6 L6,0")
    .attr("stroke", lum > 0.55 ? "#4a4a4a" : "#ffffff")
    .attr("stroke-width", 1.1);
  return `url(#hatch-${id})`;
}

function convertRemToPixels(rem) {
  return rem * parseFloat(getComputedStyle(document.documentElement).fontSize);
}

export default { render };
