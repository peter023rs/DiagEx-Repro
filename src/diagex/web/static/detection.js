"use strict";
const $ = id => document.getElementById(id);
const params = new URLSearchParams(location.search);
const runDir = params.get("run_dir") || "";
const BOX_FIELDS = ["x", "y", "w", "h"];
const MAX_ZOOM = 32;
const SELECTED_COLOR = "#c026d3";
let state, tab = "symbols", selected = null, zoom = 1;
function setting(key) { try { return localStorage.getItem(key); } catch { return null; } }
function saveSetting(key, value) { try { localStorage.setItem(key, value); } catch { /* Optional preference storage. */ } }
let language = setting("diagex.web.language") === "zh-CN" ? "zh-CN" : "en";
$("autoFocus").checked = setting("diagex.detection.autoFocus") !== "false";
const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
function t(key, values = {}) {
  return (DETECTION_I18N[language][key] ?? DETECTION_I18N.en[key] ?? String(key ?? ""))
    .replace(/\{(\w+)\}/g, (_, name) => String(values[name] ?? ""));
}
function translatedReason(value) { return value || ""; }
function applyLanguage() {
  document.documentElement.lang = language;
  document.title = `${t("title")} · DiagEx`;
  $("languageSwitch").value = language;
  for (const node of document.querySelectorAll("[data-i18n]")) node.textContent = t(node.dataset.i18n);
  $("search").placeholder = t("searchHint");
  for (const [id, key] of [["languageSwitch","language"],["items","items"],["drawing","drawing"],["zoomIn","zoomIn"],["zoomOut","zoomOut"]]) {
    $(id).setAttribute("aria-label", t(key));
  }
}
async function api(path, body) {
  const response = await fetch(path, body ? {
    method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify(body),
  } : {});
  const value = await response.json();
  if (!response.ok) throw Error(value.error || t("failed"));
  return value;
}
function error(e) {
  $("error").textContent = translatedReason(e.message);
  $("error").classList.remove("hidden");
}
function page() { return state?.pages.find(p => p.page_index === Number($("page").value)); }
function current() { return state?.[tab].find(row => row.id === selected); }
function legendType(entry) {
  if (entry.source === "built_in") return "library";
  if (entry.crop_quality === "omitted_abbreviation" || entry.attributes?.legend_kind === "abbreviation") return "text";
  return "drawing";
}
function legendTypeText(entry) { return t({drawing:"drawingLegend", text:"textLegend", library:"libraryLegend"}[legendType(entry)]); }
function rowName(row) { return (row.entry || row.detection).label || (row.entry || {}).symbol_class || row.detection?.attributes?.broad_category || t("unlabelled"); }
function rowLocation(row) {
  if (!row) return null;
  const index = row.entry ? row.entry.source_page_index : row.detection.page_index;
  const bounds = row.entry ? row.entry.source_bbox : row.detection.bbox;
  if (index == null || !bounds || !state.pages.some(p => p.page_index === index)) return null;
  return {pageIndex: index, bounds};
}
function rows() {
  const query = $("search").value.trim().toLowerCase();
  return state[tab].filter(row => {
    if (tab !== "legends" && row.detection.page_index != null && row.detection.page_index !== page().page_index) return false;
    if (tab === "legends" && $("legendType").value !== "all" && legendType(row.entry) !== $("legendType").value) return false;
    if ($("filter").value !== "all" && ($("filter").value === "uncertain" ? !["uncertain", "unreviewed", "reject", "rejected", "low"].includes(row.status) : row.status !== $("filter").value)) return false;
    const obj = row.entry || row.detection;
    if ($("kindFilter").value !== "all" && obj.kind !== $("kindFilter").value) return false;
    // Search meaningful text, never embedded thumbnail data.
    const text = [row.id, rowName(row), obj.kind, t(obj.kind), obj.symbol_class, JSON.stringify(obj.attributes || {}), row.reason, translatedReason(row.reason), t(row.origin || obj.kind)].join(" ");
    return text.toLowerCase().includes(query);
  });
}
function select(id) {
  selected = id;
  const location = rowLocation(current());
  if (location) $("page").value = String(location.pageIndex);
  render();
  if ($("autoFocus").checked) focusSelected();
}
function renderPages() {
  const prior = $("page").value;
  $("page").innerHTML = state.pages.map(p => {
    const incomplete = state.per_page_status[p.page_index] && state.per_page_status[p.page_index] !== "ok";
    return `<option value="${p.page_index}">${t("page")} ${p.page_index + 1} · ${esc(t(p.role))}${incomplete ? ` · ${t("incomplete")}` : ""}</option>`;
  }).join("");
  if (state.pages.some(p => String(p.page_index) === prior)) $("page").value = prior;
}
function render() {
  if (!state) return;
  if (!page()) { $("items").textContent = t("noItems"); $("summary").textContent = t("noPages"); return; }
  $("runName").textContent = runDir.split("/").pop();
  $("summary").textContent = `${t(state.status)} · ${t("summary", {symbols:state.observation_count, candidates:state.candidate_count, legends:state.legends.length})}${state.stop_reason ? ` · ${state.stop_reason}` : ""}`;
  for (const [id, name] of [["legendTab","legends"],["symbolTab","symbols"],["candidateTab","candidates"],["textTab","texts"]]) $(id).classList.toggle("active", tab === name);
  $("legendTypeField").hidden = tab !== "legends";
  const location = rowLocation(current());
  $("focus").disabled = !location;
  $("selectionLabel").textContent = current()
    ? location ? t("selection", {name: rowName(current()), page: location.pageIndex + 1}) : `${rowName(current())} · ${t("noSource")}`
    : t("noSelection");
  $("selectionLabel").parentElement.classList.toggle("has-selection", !!location);
  $("items").replaceChildren();
  const visible = rows();
  for (const row of visible) {
    const button = document.createElement("button");
    button.className = row.id === selected ? "selected" : "";
    button.dataset.itemId = row.id;
    button.setAttribute("aria-pressed", String(row.id === selected));
    const origin = row.entry ? legendTypeText(row.entry) : t(row.origin);
    button.innerHTML = `${esc(rowName(row))}<small>${esc(t(row.status))} · ${esc(origin)}</small>`;
    button.onclick = () => select(row.id);
    $("items").append(button);
  }
  if (!visible.length) $("items").textContent = t("noItems");
  renderDrawing();
  renderInspector();
}
function svgElement(name, attributes) {
  const element = document.createElementNS("http://www.w3.org/2000/svg", name);
  for (const [key, value] of Object.entries(attributes)) element.setAttribute(key, value);
  return element;
}
function contextBounds(bounds, sourcePage, multiplier = .4) {
  const margin = Math.max(25, Math.round(Math.max(bounds.w, bounds.h) * multiplier));
  const x = Math.max(0, bounds.x - margin), y = Math.max(0, bounds.y - margin);
  return {x, y, w: Math.min(sourcePage.width, bounds.x + bounds.w + margin) - x,
    h: Math.min(sourcePage.height, bounds.y + bounds.h + margin) - y};
}
function cropUrl(index, bounds) {
  return `/api/detection-crop?${new URLSearchParams({run_dir:runDir, page:index, box:BOX_FIELDS.map(key => bounds[key]).join(",")})}`;
}
function baseScale() {
  const p = page(), viewport = $("viewport");
  return Math.max(.001, Math.min((viewport.clientWidth - 32) / p.width, (viewport.clientHeight - 32) / p.height));
}
function viewportCenter() {
  const matrix = $("drawing").getScreenCTM();
  if (!matrix) return null;
  const rect = $("viewport").getBoundingClientRect();
  return new DOMPoint(rect.left + $("viewport").clientWidth / 2, rect.top + $("viewport").clientHeight / 2).matrixTransform(matrix.inverse());
}
function centerOn(point) {
  const viewport = $("viewport"), rect = viewport.getBoundingClientRect();
  const target = new DOMPoint(point.x, point.y).matrixTransform($("drawing").getScreenCTM());
  viewport.scrollLeft += target.x - rect.left - viewport.clientWidth / 2;
  viewport.scrollTop += target.y - rect.top - viewport.clientHeight / 2;
}
function focusSelected() {
  const location = rowLocation(current());
  if (!location) return;
  if (location.pageIndex !== page().page_index) $("page").value = String(location.pageIndex);
  const b = location.bounds, viewport = $("viewport");
  const scale = Math.min(viewport.clientWidth * .48 / Math.max(1, b.w), viewport.clientHeight * .48 / Math.max(1, b.h));
  zoom = Math.max(1, Math.min(MAX_ZOOM, scale / baseScale()));
  renderDrawing();
  centerOn({x:b.x + b.w / 2, y:b.y + b.h / 2});
}
function setZoom(value) {
  const center = viewportCenter();
  zoom = Math.max(.25, Math.min(MAX_ZOOM, value));
  renderDrawing();
  if (center) centerOn(center);
}
function renderDrawing() {
  const p = page(), svg = $("drawing");
  svg.replaceChildren();
  $("comparison").className = $("layout").value;
  svg.setAttribute("viewBox", `0 0 ${p.width} ${p.height}`);
  const scale = baseScale() * zoom;
  svg.style.width = `${p.width * scale}px`;
  svg.style.height = `${p.height * scale}px`;
  $("zoomLabel").textContent = `${Math.round(zoom * 100)}%`;
  const sourceLayer = svgElement("g", {class:"source-layer"});
  svg.append(sourceLayer);
  sourceLayer.append(svgElement("image", {href:`/api/detection-page?${new URLSearchParams({run_dir:runDir, page:p.page_index})}`, width:p.width, height:p.height}));
  const location = rowLocation(current());
  const active = location && location.pageIndex === p.page_index ? location.bounds : null;
  if (active) {
    const context = contextBounds(active, p, 1.5);
    // Re-render the local PDF region so automatic zoom does not magnify a blurry preview.
    sourceLayer.append(svgElement("image", {href:cropUrl(p.page_index, context), x:context.x, y:context.y, width:context.w, height:context.h, class:"focused-source"}));
  }
  const boxes = rows().filter(row => rowLocation(row)?.pageIndex === p.page_index);
  for (const row of boxes) {
    if (row.id === selected) continue;
    const b = rowLocation(row).bounds;
    const color = row.origin === "detected" ? "#12804d" : row.status === "non_symbol" ? "#7e8792" : "#d47d00";
    const rect = svgElement("rect", {x:b.x, y:b.y, width:b.w, height:b.h, stroke:color, fill:color,
      class:active ? "other-item muted" : "other-item", "data-item-id":row.id});
    if (row.status === "non_symbol") rect.setAttribute("stroke-dasharray", "4 4");
    rect.onclick = () => { select(row.id); };
    rect.setAttribute("tabindex", "0"); rect.setAttribute("role", "button");
    rect.setAttribute("aria-label", rowName(row));
    rect.onkeydown = event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); select(row.id); } };
    const title = svgElement("title", {});
    title.textContent = `${rowName(row)} · ${t(row.status)}`;
    rect.append(title);
    svg.append(rect);
  }
  if (active) {
    // The white halo and magenta outline stay visible across dense black strokes.
    for (const [className, stroke] of [["selection-halo", "#ffffff"], ["active", SELECTED_COLOR]]) {
      svg.append(svgElement("rect", {x:active.x, y:active.y, width:active.w, height:active.h,
        stroke, fill:SELECTED_COLOR, class:className, "data-item-id":selected}));
    }
  }
  const original = $("sourceDrawing");
  original.replaceChildren(...[...svg.querySelectorAll("image")].map(image => image.cloneNode(true)));
  original.setAttribute("viewBox", svg.getAttribute("viewBox"));
  original.style.width = svg.style.width; original.style.height = svg.style.height;
  const opacity = {full:1, dim:.25, hidden:0}[$("background").value];
  sourceLayer.setAttribute("opacity", opacity);

}
function renderInspector() {
  const row = current();
  if (!row) { $("inspector").innerHTML = `<p>${esc(t("selectHint"))}</p>`; return; }
  const obj = row.entry || row.detection;
  let html = `<h3>${esc(rowName(row))}</h3><span class="origin-badge">${esc(row.entry ? legendTypeText(obj) : t(row.origin))}</span><p>${esc(translatedReason(row.reason))}</p>`;
  if (row.entry?.image_b64) html += `<img alt="${esc(t("sourceCrop"))}" src="data:image/png;base64,${esc(obj.image_b64)}">`;
  const location = rowLocation(row);
  if (location) {
    const b = location.bounds, p = state.pages.find(p => p.page_index === location.pageIndex);
    const context = contextBounds(b, p), url = cropUrl(location.pageIndex, context);
    html += `<a target="_blank" rel="noopener" href="${url}" class="detail-link"><svg class="source-detail" viewBox="0 0 ${context.w} ${context.h}" role="img" aria-label="${esc(t("sourceDetail"))}"><image href="${url}" width="${context.w}" height="${context.h}"/><rect x="${b.x-context.x}" y="${b.y-context.y}" width="${b.w}" height="${b.h}"/></svg></a><small>${esc(t("sourceDetail"))}</small>`;
  }
  html += "<dl>";
  for (const key of ["id","label","kind","symbol_class","description","confidence","page_index","tile_id","bbox","source_page_index","source_bbox","source","raw_text","source_text_ids","source_path_ids","attributes"]) {
    if (obj[key] == null) continue;
    html += `<dt>${esc(t(key))}</dt><dd>${esc(typeof obj[key] === "object" ? JSON.stringify(obj[key], null, 2) : ["kind", "confidence"].includes(key) ? t(obj[key]) : obj[key])}</dd>`;
  }
  html += "</dl>";
  if (row.diagnostics) html += `<details><summary>${esc(t("diagnostics"))}</summary><pre>${esc(JSON.stringify(row.diagnostics, null, 2))}</pre></details>`;
  $("inspector").innerHTML = html;
}
for (const [id, name] of [["legendTab","legends"],["symbolTab","symbols"],["candidateTab","candidates"],["textTab","texts"]]) $(id).onclick = () => {
  tab = name; selected = null; render();
};
$("page").onchange = () => { selected = null; zoom = 1; render(); };
for (const id of ["filter","search","legendType","kindFilter"]) $(id).addEventListener(id === "search" ? "input" : "change", () => {
  if (!rows().some(row => row.id === selected)) selected = null;
  render();
});
for (const id of ["layout","background"]) $(id).onchange = () => { renderDrawing(); if (current() && $("autoFocus").checked) focusSelected(); };
for (const [id, panel] of [["toggleList","list"],["toggleInspector","inspector"]]) $(id).onclick = () => {
  const hidden = document.querySelector(".review-layout").classList.toggle(`hide-${panel}`);
  $(id).setAttribute("aria-pressed", String(!hidden)); renderDrawing();
};
for (const id of ["viewport", "sourceViewport"]) {
  const viewport = $(id); let pan = null;
  viewport.onpointerdown = event => {
    if (event.button !== 0 || event.target.closest("rect")) return;
    pan = {x:event.clientX, y:event.clientY, left:viewport.scrollLeft, top:viewport.scrollTop};
    viewport.setPointerCapture(event.pointerId);
  };
  viewport.onpointermove = event => { if (pan) { viewport.scrollLeft = pan.left + pan.x - event.clientX; viewport.scrollTop = pan.top + pan.y - event.clientY; } };
  viewport.onpointerup = viewport.onpointercancel = () => { pan = null; };
  viewport.onscroll = () => {
    const other = $(id === "viewport" ? "sourceViewport" : "viewport");
    if (other.scrollLeft !== viewport.scrollLeft) other.scrollLeft = viewport.scrollLeft;
    if (other.scrollTop !== viewport.scrollTop) other.scrollTop = viewport.scrollTop;
  };
}
$("zoomIn").onclick = () => setZoom(zoom * 1.4);
$("zoomOut").onclick = () => setZoom(zoom / 1.4);
$("fit").onclick = () => { zoom = 1; renderDrawing(); $("viewport").scrollTo(0,0); };
$("focus").onclick = focusSelected;
$("autoFocus").onchange = () => { saveSetting("diagex.detection.autoFocus", String($("autoFocus").checked)); if ($("autoFocus").checked) focusSelected(); };
$("languageSwitch").onchange = () => {
  language = $("languageSwitch").value;
  saveSetting("diagex.web.language", language);
  applyLanguage();
  if (state) { renderPages(); render(); }

};
async function load() {
  try {
    const initial = !state;
    state = await api(`/api/detections?${new URLSearchParams({run_dir:runDir})}`);
    $("error").classList.add("hidden"); renderPages();
    if (initial && state.symbols.length) $("page").value = String(state.symbols[0].detection.page_index);
    render();
    if (!state.source_available) error(new Error(t("missingSource")));
  } catch (e) { error(e); }
}
$("reload").onclick = load;
let resizeTimer;
window.addEventListener("resize", () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => { if (state) { if (current() && $("autoFocus").checked) focusSelected(); else renderDrawing(); } }, 100);
});
for (const kind of ["detection", "legend"]) {
  const link = $(kind === "detection" ? "downloadDetection" : "downloadLegend");
  link.href = `/api/detection-download?${new URLSearchParams({run_dir:runDir, kind})}`;
  link.download = `${kind}.json`;
}
applyLanguage();
load();
