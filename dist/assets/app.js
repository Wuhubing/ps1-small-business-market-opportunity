const DATA = "data/";
const COLORS = { teal: "#006d68", dark: "#102a36", lime: "#c8e35b", gold: "#e8ae43", pale: "#e8efed" };

async function initMarketOpportunity() {
  const hypotheses = {
    "Food services": {code:"722", concept:"Small-format prepared-food or shared-kitchen pilot", evidence:"15 cottage-food permits provide a possible opt-in operator pathway; 13 persistent vacancies under 1,500 sqft provide spaces to investigate. Neither measures buyer demand or food-use suitability.", test:"Compare nearby menus and prices, test the preferred cuisine and acceptable price band anonymously, then record paid orders and repeat purchases in aggregate."},
    "Retail trade": {code:"44–45", concept:"A focused product-category pop-up", evidence:"Regional retail establishments show existing business supply. The storefront inventory can guide where to investigate a temporary space, but contains no product preferences or sales.", test:"Choose a specific product category, compare local assortments and prices, and measure paid conversion, average basket and repeat purchase frequency in a short pilot."},
    "Personal services": {code:"812", concept:"An appointment-based personal-service pilot", evidence:"Regional employer counts and average staffing provide sector context, not evidence that a particular service is missing locally. The broad category includes businesses with very different needs.", test:"Select a specific service, check local availability and prices, and measure aggregate bookings, willingness to pay and repeat visits. Verify licensing and fit-out requirements."}
  };
  const category = document.getElementById("market-category");
  function drawHypothesis() {
    const item = hypotheses[category.value];
    document.getElementById("market-hypothesis").innerHTML = `<h4>${item.concept}</h4><p><strong>Observed basis:</strong> ${item.evidence}</p><p><strong>Validation needed:</strong> ${item.test}</p>`;
  }
  function calculate() {
    const values = ["price","variable","fixed","days"].map(key => {
      const input = document.getElementById(`market-${key}`);
      return input.value.trim() === "" ? NaN : Number(input.value);
    });
    const [price, variable, fixed, days] = values;
    const result = document.getElementById("market-result");
    if (!values.every(Number.isFinite) || price <= 0 || variable < 0 || fixed < 0 || days < 1 || days > 31 || !Number.isInteger(days)) {
      result.textContent = "Enter valid costs and a whole number of trading days from 1 to 31."; return;
    }
    if (price <= variable) { result.textContent = "No positive contribution per sale: change the price or cost assumption before estimating break-even."; return; }
    const daily = Math.ceil(fixed / (price-variable) / days);
    result.textContent = `Scenario only: at least ${daily.toLocaleString()} sales per trading day, with $${(price-variable).toFixed(2)} contribution per sale. This is required sales volume, not evidence that customers will buy.`;
  }
  category.addEventListener("change", drawHypothesis); drawHypothesis();
  document.querySelectorAll('.scenario-inputs input').forEach(el=>el.addEventListener('input',calculate)); calculate();
  try {
    const industry = await loadJSON("industry_structure.json");
    const county = document.getElementById("market-county");
    function drawTable() {
      document.getElementById("market-table").innerHTML = industry.cbp_2022.filter(r=>r.county===county.value).map(row=>
        `<tr><td>${row.industry} (${hypotheses[row.industry].code})</td><td>${row.establishments.toLocaleString()}</td><td>${row.employment.toLocaleString()}</td><td>${row.establishments > 0 ? (row.employment / row.establishments).toFixed(1) : "Not available"}</td></tr>`).join("");
    }
    county.addEventListener("change",drawTable); drawTable();
  } catch (error) { document.getElementById("market-table").innerHTML = '<tr><td colspan="4">Category evidence is unavailable. Please reload.</td></tr>'; }
}

async function loadJSON(name) {
  const response = await fetch(`${DATA}${name}`);
  if (!response.ok) throw new Error(`Could not load ${name}`);
  return response.json();
}

function showError(id, error) {
  const node = document.getElementById(id);
  if (node) node.innerHTML = `<p class="status error">Data could not be loaded. ${error.message}</p>`;
}

const baseConfig = {
  background: null,
  axis: { labelColor: COLORS.dark, titleColor: COLORS.dark, gridColor: "#dfe8e6", labelFontSize: 12, titleFontSize: 13 },
  legend: { labelColor: COLORS.dark, titleColor: COLORS.dark, labelFontSize: 12 },
  view: { stroke: null },
};

async function initHome() {
  try {
    const [findings, districts, ages, licenses] = await Promise.all([
      loadJSON("findings.json"), loadJSON("district_summary.json"),
      loadJSON("vacancy_age_buckets.json"), loadJSON("licenses_by_year.json"),
    ]);
    document.getElementById("headline-value").textContent = findings.headline.value;
    document.getElementById("snapshot-label").textContent = findings.snapshot;
    findings.findings.forEach((finding, index) => {
      const value = document.querySelector(`[data-kpi="${index}"] .value`);
      const copy = document.querySelector(`[data-kpi="${index}"] p`);
      value.textContent = finding.unit === "percent" ? `${finding.value}%` : finding.value.toLocaleString();
      copy.textContent = finding.text;
    });
    document.getElementById("findings-list").innerHTML = findings.findings.map(item =>
      `<article class="finding"><span class="id">${item.id}</span><p>${item.text}</p><small>${item.method}</small></article>`
    ).join("");
    document.getElementById("recommendations-list").innerHTML = findings.recommendations.map(item =>
      `<article class="recommendation"><span class="id">${item.id} · ${item.supported_by.join(", ")}</span><p>${item.text}</p><small>${item.action}</small></article>`
    ).join("");
    document.getElementById("district-table-body").innerHTML = districts.map((row, index) =>
      `<tr><td>${index + 1}</td><td><strong>${row.district}</strong></td><td class="numeric">${row.vacant_storefronts}</td><td class="numeric">${row.average_vacancy_months ?? "—"}</td><td class="numeric">${row.long_term_storefronts}</td><td class="numeric">${row.area_known}/${row.vacant_storefronts}</td></tr>`
    ).join("");

    await vegaEmbed("#district-chart", {
      $schema: "https://vega.github.io/schema/vega-lite/v5.json", width: "container", height: 330,
      data: { values: districts },
      mark: { type: "bar", cornerRadiusEnd: 5 },
      encoding: {
        y: { field: "district", type: "nominal", sort: "-x", title: null },
        x: { field: "vacant_storefronts", type: "quantitative", title: "Vacant storefronts" },
        color: { field: "average_vacancy_months", type: "quantitative", title: "Estimated avg. months", scale: { range: [COLORS.lime, COLORS.teal] } },
        tooltip: [
          { field: "district", title: "District" }, { field: "vacant_storefronts", title: "Storefronts" },
          { field: "average_vacancy_months", title: "Avg. vacancy months" }, { field: "long_term_storefronts", title: ">12 months" },
        ],
      }, config: baseConfig,
    }, { actions: false, renderer: "svg" });

    const ageTotals = Object.values(ages.reduce((acc, row) => {
      const key = `${row.age_bucket}|${row.area_bucket}`;
      acc[key] = acc[key] || { age_bucket: row.age_bucket, area_bucket: row.area_bucket, storefronts: 0 };
      acc[key].storefronts += row.storefronts;
      return acc;
    }, {}));
    await vegaEmbed("#age-chart", {
      $schema: "https://vega.github.io/schema/vega-lite/v5.json", width: "container", height: 330,
      data: { values: ageTotals }, mark: { type: "rect", cornerRadius: 3 },
      encoding: {
        x: { field: "area_bucket", type: "nominal", title: "Reported floor area", sort: ["<1,000 sqft", "1,000–2,500 sqft", ">2,500 sqft", "Area not reported"] },
        y: { field: "age_bucket", type: "nominal", title: "Estimated vacancy duration", sort: [">12 months", "6–12 months", "3–6 months", "<3 months"] },
        color: { field: "storefronts", type: "quantitative", scale: { range: ["#edf4d0", COLORS.teal] }, title: "Storefronts" },
        tooltip: [{ field: "age_bucket" }, { field: "area_bucket" }, { field: "storefronts" }],
      }, config: baseConfig,
    }, { actions: false, renderer: "svg" });

    await vegaEmbed("#license-chart", {
      $schema: "https://vega.github.io/schema/vega-lite/v5.json", width: "container", height: 300,
      data: { values: licenses }, mark: { type: "line", point: true, strokeWidth: 3 },
      encoding: {
        x: { field: "year", type: "ordinal", title: "License-added year" },
        y: { field: "new_licenses", type: "quantitative", title: "Records added" },
        color: { field: "licensecat", type: "nominal", title: "License category", scale: { range: [COLORS.teal, COLORS.gold] } },
        tooltip: [{ field: "year" }, { field: "licensecat", title: "Category" }, { field: "new_licenses", title: "Records" }],
      }, config: baseConfig,
    }, { actions: false, renderer: "svg" });
  } catch (error) { showError("home-data", error); }
}

let exploreState = { rows: [], licenses: [], districts: [], view: null, activeView: "storefronts" };

function exploreQuery() {
  const params = new URLSearchParams(location.search);
  return {
    districts: params.get("districts")?.split("|").filter(Boolean) || [],
    minArea: Number(params.get("minArea") || 0), maxArea: Number(params.get("maxArea") || 110000),
    minMonths: Number(params.get("minMonths") || 0), startYear: Number(params.get("startYear") || 2014),
    endYear: Number(params.get("endYear") || 2026), view: params.get("view") || "storefronts",
  };
}

function currentExploreFilters() {
  return {
    districts: [...document.querySelectorAll("#district-options input:checked")].map(el => el.value),
    minArea: Number(document.getElementById("min-area").value || 0), maxArea: Number(document.getElementById("max-area").value || 110000),
    minMonths: Number(document.getElementById("min-months").value || 0), startYear: Number(document.getElementById("start-year").value || 2014),
    endYear: Number(document.getElementById("end-year").value || 2026), view: exploreState.activeView,
  };
}

function filterExploreData() {
  const filters = currentExploreFilters();
  const rows = exploreState.rows.filter(row =>
    filters.districts.includes(row.district) && (row.square_feet === null || (row.square_feet >= filters.minArea && row.square_feet <= filters.maxArea)) &&
    row.vacancy_months >= filters.minMonths
  );
  const licenses = exploreState.licenses.filter(row => row.year >= filters.startYear && row.year <= filters.endYear);
  const count = licenses.reduce((sum, row) => sum + row.new_licenses, 0);
  document.getElementById("month-output").textContent = filters.minMonths;
  document.getElementById("result-count").textContent = `${rows.length} storefront records · ${count.toLocaleString()} license records in selected years`;
  const params = new URLSearchParams({
    districts: filters.districts.join("|"), minArea: filters.minArea, maxArea: filters.maxArea,
    minMonths: filters.minMonths, startYear: filters.startYear, endYear: filters.endYear, view: filters.view,
  });
  history.replaceState(null, "", `?${params}`);
  return { rows, licenses };
}

function exploreSpec(kind, data) {
  const common = { $schema: "https://vega.github.io/schema/vega-lite/v5.json", width: "container", height: 430, data: { name: "filtered", values: data }, config: baseConfig };
  if (kind === "storefronts") return { ...common, mark: { type: "circle", opacity: 0.78, size: 110 }, encoding: {
    x: { field: "square_feet", type: "quantitative", title: "Reported floor area (sqft)" },
    y: { field: "vacancy_months", type: "quantitative", title: "Estimated vacancy duration (months)" },
    color: { field: "district", type: "nominal", title: "District" },
    tooltip: [{ field: "district" }, { field: "square_feet", title: "Square feet" }, { field: "vacancy_months", title: "Vacancy months" }],
  }};
  if (kind === "districts") return { ...common, transform: [{ aggregate: [{ op: "count", as: "storefronts" }, { op: "mean", field: "vacancy_months", as: "avg_months" }], groupby: ["district"] }], mark: { type: "bar", cornerRadiusEnd: 5 }, encoding: {
    y: { field: "district", type: "nominal", sort: "-x", title: null }, x: { field: "storefronts", type: "quantitative", title: "Filtered storefronts" },
    color: { field: "avg_months", type: "quantitative", scale: { range: [COLORS.lime, COLORS.teal] }, title: "Avg. months" },
    tooltip: [{ field: "district" }, { field: "storefronts" }, { field: "avg_months", format: ".1f" }],
  }};
  if (kind === "profile") return { ...common, mark: { type: "bar" }, encoding: {
    x: { field: "age_bucket", type: "nominal", title: "Estimated vacancy duration", sort: ["<3 months", "3–6 months", "6–12 months", ">12 months"] },
    y: { aggregate: "count", type: "quantitative", title: "Storefronts" }, color: { field: "area_bucket", type: "nominal", title: "Floor area" },
    tooltip: [{ field: "age_bucket" }, { field: "area_bucket" }, { aggregate: "count", title: "Storefronts" }],
  }};
  return { ...common, mark: { type: "line", point: true, strokeWidth: 3 }, encoding: {
    x: { field: "year", type: "ordinal", title: "License-added year" }, y: { field: "new_licenses", type: "quantitative", title: "Records added" },
    color: { field: "licensecat", type: "nominal", title: "Category", scale: { range: [COLORS.teal, COLORS.gold] } },
    tooltip: [{ field: "year" }, { field: "licensecat" }, { field: "new_licenses" }],
  }};
}

async function renderExploreView() {
  const filtered = filterExploreData();
  const values = exploreState.activeView === "licenses" ? filtered.licenses : filtered.rows;
  const result = await vegaEmbed("#explore-chart", exploreSpec(exploreState.activeView, values), { actions: false, renderer: "svg" });
  exploreState.view = result.view;
  document.querySelectorAll(".view-button").forEach(button => button.classList.toggle("active", button.dataset.view === exploreState.activeView));
  document.getElementById("explore-source").innerHTML = exploreState.activeView === "licenses"
    ? 'Source: <a href="https://data.boston.gov/dataset/food-establishment-inspections" target="_blank" rel="noopener">Boston food establishment licenses</a>; accessed 2026-09-21; unit: license records added.'
    : 'Source: <a href="https://data.cambridgema.gov/resource/swpv-8j3w.json" target="_blank" rel="noopener">Cambridge Vacant Storefronts</a>; accessed 2026-09-21; units: storefronts, estimated months, square feet.';
}

async function updateExplore() {
  const filtered = filterExploreData();
  const values = exploreState.activeView === "licenses" ? filtered.licenses : filtered.rows;
  if (!exploreState.view) return renderExploreView();
  const change = vega.changeset().remove(() => true).insert(values);
  await exploreState.view.change("filtered", change).runAsync();
}

async function initExplore() {
  try {
    const query = exploreQuery();
    [exploreState.rows, exploreState.licenses] = await Promise.all([loadJSON("vacancy_rows.json"), loadJSON("licenses_by_year.json")]);
    exploreState.districts = [...new Set(exploreState.rows.map(row => row.district))].sort();
    const selected = query.districts.length ? query.districts : exploreState.districts;
    document.getElementById("district-options").innerHTML = exploreState.districts.map(district =>
      `<label><input type="checkbox" value="${district}" ${selected.includes(district) ? "checked" : ""}> <span>${district}</span></label>`
    ).join("");
    document.getElementById("min-area").value = query.minArea;
    document.getElementById("max-area").value = query.maxArea;
    document.getElementById("min-months").value = query.minMonths;
    document.getElementById("start-year").value = query.startYear;
    document.getElementById("end-year").value = query.endYear;
    exploreState.activeView = query.view;
    document.getElementById("filter-panel").addEventListener("input", updateExplore);
    document.querySelectorAll(".view-button").forEach(button => button.addEventListener("click", async () => {
      exploreState.activeView = button.dataset.view;
      await renderExploreView();
    }));
    await renderExploreView();
  } catch (error) { showError("explore-chart", error); }
}

async function initMap() {
  try {
    const [points, districts] = await Promise.all([loadJSON("license_points.json"), loadJSON("district_summary.json")]);
    document.getElementById("map").innerHTML = "";
    const map = L.map("map", { preferCanvas: true }).setView([42.355, -71.09], 12);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>', maxZoom: 19,
    }).addTo(map);
    const layer = L.layerGroup().addTo(map);
    const category = document.getElementById("map-category");
    const year = document.getElementById("map-year");
    const years = [...new Set(points.map(point => point.year))].sort((a, b) => a - b);
    year.innerHTML = '<option value="all">All years</option>' + years.map(item => `<option value="${item}">${item}</option>`).join("");
    function draw() {
      layer.clearLayers();
      const filtered = points.filter(point => (category.value === "all" || point.license_category === category.value) && (year.value === "all" || point.year === Number(year.value)));
      filtered.forEach(point => L.circleMarker([point.lat, point.lng], {
        radius: 3.5, color: point.license_category === "FS" ? COLORS.teal : COLORS.gold,
        fillColor: point.license_category === "FS" ? COLORS.teal : COLORS.gold, fillOpacity: 0.55, weight: 0.5,
      }).bindPopup(`<strong>License category:</strong> ${point.license_category}<br><strong>Added:</strong> ${point.year}<br><strong>ZIP:</strong> ${point.zip || "Not reported"}`).addTo(layer));
      document.getElementById("map-count").textContent = `${filtered.length.toLocaleString()} license records shown`;
    }
    category.addEventListener("change", draw); year.addEventListener("change", draw); draw();
    document.getElementById("map-district-table").innerHTML = districts.slice(0, 5).map(row =>
      `<tr><td>${row.district}</td><td class="numeric">${row.vacant_storefronts}</td><td class="numeric">${row.average_vacancy_months}</td></tr>`
    ).join("");
  } catch (error) { showError("map", error); }
}

async function initQuality() {
  try {
    const report = await loadJSON("quality_report.json");
    const body = document.getElementById("quality-table-body");
    if (body) body.innerHTML = report.metrics.map(row =>
      `<tr><td>${row.dataset}</td><td>${row.field}</td><td>${row.scope}</td><td class="numeric">${row.missing_percent}%</td></tr>`
    ).join("");
  } catch (error) { showError("quality-table", error); }
}

document.addEventListener("DOMContentLoaded", () => {
  const page = document.body.dataset.page;
  if (page === "home") { initHome(); initMarketOpportunity(); }
  if (page === "explore") initExplore();
  if (page === "map") initMap();
  if (page === "data" || page === "reflection") initQuality();
});
