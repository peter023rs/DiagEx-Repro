"use strict";

const el = id => document.getElementById(id);
const I18N = {
  en: {
    title: "DiagEx Review", humanReview: "human review", previousPage: "Previous page", nextPage: "Next page",
    pageRole: "Page role", approvePage: "Approve page", waive: "Waive", zoomOut: "Zoom out", zoomIn: "Zoom in",
    fit: "Fit", inferenceBackground: "Inference background", backgroundFull: "PDF + overlays",
    backgroundDim: "Dimmed PDF", backgroundNone: "Overlays only", language: "Language", undo: "Undo",
    finishExport: "Finish & export", reviewQueue: "Review queue", loading: "Loading…", needsReview: "Needs review",
    allItems: "All items", allTypes: "All types", entities: "Entities", connections: "Connections", conflicts: "Conflicts",
    originalSource: "Original source", originalPidPage: "Original P&ID page", editableExtraction: "Editable extraction",
    reviewed: "reviewed", pending: "pending", rejected: "rejected", inferenceFrame: "Inference rendering frame",
    inspector: "Inspector", drawMissingEntity: "Draw missing entity", addConnection: "Add connection",
    comparisonView: "Comparison view", comparisonLayout: "Comparison layout", sideBySide: "Side by side", stacked: "Stacked",
    hideQueue: "Hide queue", showQueue: "Show queue", hideInspector: "Hide inspector", showInspector: "Show inspector",
    selectItem: "Select an entity, connection, or conflict.", pageCount: "Page {current} / {count}", pageShort: "page {page}",
    remaining: "{count} remaining", readyExport: "Ready to export", noMatches: "Nothing matches this filter.",
    entity: "entity", connection: "connection", conflict: "conflict", graphConflict: "Graph conflict",
    modelConfidence: "model confidence", review: "review", label: "Label", kind: "Kind",
    equipmentClass: "Equipment class", valveType: "Valve type", instrumentFunction: "Instrument function",
    attributesJson: "Attributes (JSON)", from: "From", to: "To", lineType: "Line type",
    polylineJson: "Polyline points (JSON)", saveChanges: "Save changes", approve: "Approve", reject: "Reject",
    resolved: "Resolved", waiveReason: "Waive with reason", rejectReason: "Reason for rejection (optional)",
    resolveReason: "How was this resolved? (optional)", conflictWaiveReason: "Reason for waiving this conflict",
    pageWaiveReason: "Reason for waiving this page", actionSaved: "{operation} saved",
    drawInstruction: "Drag a box around the missing entity in the editable pane",
    twoEntitiesRequired: "At least two active entities are required", fromEntityPrompt: "From entity ID or exact label",
    toEntityPrompt: "To entity ID or exact label", unresolvedEntity: "Could not resolve one of those entities",
    exportSuccess: "Reviewed DEXPI JSON and XML exported", loadFailed: "Failed to load review: {message}",
    unlabelled: "unlabelled", reasonPartialPage: "partial page", reasonGraphConflict: "graph conflict",
    reasonBuildIssue: "build issue", reasonMediumConfidence: "medium confidence", reasonLowConfidence: "low confidence",
    reasonUnclassified: "unclassified", reasonDanglingEndpoint: "dangling endpoint",
    warningMalformedAudit: "ignored malformed events.jsonl line {line}",
    warningMissingPage: "node {node} references missing page {page}",
    warningOutsidePage: "node {node} falls outside rendered page {page}"
  },
  "zh-CN": {
    title: "DiagEx 人工复核", humanReview: "人工复核", previousPage: "上一页", nextPage: "下一页",
    pageRole: "页面类型", approvePage: "批准本页", waive: "豁免", zoomOut: "缩小", zoomIn: "放大",
    fit: "适应窗口", inferenceBackground: "推断视图背景", backgroundFull: "PDF + 标注层",
    backgroundDim: "淡化 PDF", backgroundNone: "仅显示标注层", language: "语言", undo: "撤销",
    finishExport: "完成并导出", reviewQueue: "复核队列", loading: "正在加载…", needsReview: "待复核",
    allItems: "全部项目", allTypes: "全部类型", entities: "实体", connections: "连接", conflicts: "冲突",
    originalSource: "原始图纸", originalPidPage: "原始 P&ID 页面", editableExtraction: "可编辑提取结果",
    reviewed: "已复核", pending: "待处理", rejected: "已拒绝", inferenceFrame: "推断结果渲染页面",
    inspector: "属性检查器", drawMissingEntity: "框选缺失实体", addConnection: "添加连接",
    comparisonView: "对照视图", comparisonLayout: "对照布局", sideBySide: "左右排列", stacked: "上下排列",
    hideQueue: "隐藏队列", showQueue: "显示队列", hideInspector: "隐藏检查器", showInspector: "显示检查器",
    selectItem: "请选择实体、连接或冲突。", pageCount: "第 {current} / {count} 页", pageShort: "第 {page} 页",
    remaining: "剩余 {count} 项", readyExport: "可以导出", noMatches: "没有符合当前筛选条件的项目。",
    entity: "实体", connection: "连接", conflict: "冲突", graphConflict: "图结构冲突",
    modelConfidence: "模型置信度", review: "复核状态", label: "标签", kind: "种类",
    equipmentClass: "设备类别", valveType: "阀门类型", instrumentFunction: "仪表功能",
    attributesJson: "属性（JSON）", from: "起点", to: "终点", lineType: "线型",
    polylineJson: "折线坐标（JSON）", saveChanges: "保存修改", approve: "批准", reject: "拒绝",
    resolved: "已解决", waiveReason: "填写理由并豁免", rejectReason: "拒绝理由（可选）",
    resolveReason: "如何解决此问题？（可选）", conflictWaiveReason: "请输入豁免此冲突的理由",
    pageWaiveReason: "请输入豁免本页的理由", actionSaved: "已保存：{operation}",
    drawInstruction: "请在可编辑视图中拖动鼠标，框选缺失实体",
    twoEntitiesRequired: "至少需要两个有效实体", fromEntityPrompt: "请输入起点实体 ID 或完整标签",
    toEntityPrompt: "请输入终点实体 ID 或完整标签", unresolvedEntity: "无法找到其中一个实体",
    exportSuccess: "已导出复核后的 DEXPI JSON 和 XML", loadFailed: "复核页面加载失败：{message}",
    unlabelled: "未命名", reasonPartialPage: "页面提取不完整", reasonGraphConflict: "图结构冲突",
    reasonBuildIssue: "构建问题", reasonMediumConfidence: "中置信度", reasonLowConfidence: "低置信度",
    reasonUnclassified: "未分类", reasonDanglingEndpoint: "连接端点悬空",
    warningMalformedAudit: "已忽略 events.jsonl 中格式错误的第 {line} 行",
    warningMissingPage: "节点 {node} 引用了不存在的第 {page} 页",
    warningOutsidePage: "节点 {node} 位于第 {page} 页的渲染范围之外"
  }
};

const VALUE_LABELS_ZH = {
  unreviewed: "未复核", approved: "已批准", modified: "已修改", rejected: "已拒绝", waived: "已豁免", resolved: "已解决",
  approve: "批准", modify: "修改", reject: "拒绝", waive: "豁免", resolve: "解决", add: "添加", undo: "撤销",
  high: "高", medium: "中", low: "低", pid: "P&ID", legend: "图例", cover: "封面", notes: "说明", other: "其他",
  equipment: "设备", instrument: "仪表", line: "管线", connection: "连接", text: "文字", note: "注释", opc: "跨页连接",
  process: "工艺管线", signal_electric: "电信号线", signal_pneumatic: "气动信号线",
  instrument_capillary: "仪表毛细管", electrical_power: "电源线",
  iou_grey_zone: "重叠判定不明确", unstitched_line_endpoint: "管线端点未拼接",
  dropped_edge_unsnappable: "丢弃的连接无法吸附", ambiguous_opc: "跨页连接不明确"
};

function storedSetting(key) {
  try { return localStorage.getItem(key); } catch (_) { return null; }
}

function storeSetting(key, value) {
  try { localStorage.setItem(key, String(value)); } catch (_) { /* Setting still applies for this tab. */ }
}

const storedLayout = storedSetting("diagex.review.layout");
const app = {
  state: null, page: 0, zoom: 1, selection: null, syncing: false, drawMode: false,
  lang: storedSetting("diagex.review.language") === "zh-CN" ? "zh-CN" : "en",
  layout: ["side-by-side", "stacked"].includes(storedLayout) ? storedLayout : (window.matchMedia("(max-width: 1600px)").matches ? "stacked" : "side-by-side"),
  queueVisible: storedSetting("diagex.review.queueVisible") !== "false",
  inspectorVisible: storedSetting("diagex.review.inspectorVisible") !== "false"
};

function t(key, variables = {}) {
  const template = I18N[app.lang]?.[key] ?? I18N.en[key] ?? key;
  return template.replace(/\{(\w+)\}/g, (_, name) => String(variables[name] ?? `{${name}}`));
}

function displayValue(value) {
  if (value == null || value === "") return "";
  if (app.lang === "zh-CN" && VALUE_LABELS_ZH[value]) return VALUE_LABELS_ZH[value];
  return String(value);
}

function translateReason(reason) {
  const keys = {
    "partial page": "reasonPartialPage", "graph conflict": "reasonGraphConflict", "build issue": "reasonBuildIssue",
    "medium confidence": "reasonMediumConfidence", "low confidence": "reasonLowConfidence",
    unclassified: "reasonUnclassified", "dangling endpoint": "reasonDanglingEndpoint"
  };
  return keys[reason] ? t(keys[reason]) : reason;
}

function translateWarning(warning) {
  let match = /^ignored malformed events\.jsonl line (\d+)$/.exec(warning);
  if (match) return t("warningMalformedAudit", {line: match[1]});
  match = /^node (\S+) references missing page (\d+)$/.exec(warning);
  if (match) return t("warningMissingPage", {node: match[1], page: match[2]});
  match = /^node (\S+) falls outside rendered page (\d+)$/.exec(warning);
  if (match) return t("warningOutsidePage", {node: match[1], page: match[2]});
  return warning;
}

function applyLanguage() {
  document.documentElement.lang = app.lang;
  document.title = t("title");
  document.querySelectorAll("[data-i18n]").forEach(node => { node.textContent = t(node.dataset.i18n); });
  document.querySelectorAll("[data-i18n-title]").forEach(node => { node.title = t(node.dataset.i18nTitle); });
  document.querySelectorAll("[data-i18n-aria-label]").forEach(node => { node.setAttribute("aria-label", t(node.dataset.i18nAriaLabel)); });
  document.querySelectorAll("[data-i18n-alt]").forEach(node => { node.alt = t(node.dataset.i18nAlt); });
  el("languageSwitch").value = app.lang;
}

function applyWorkspaceLayout(refit = true) {
  const workspace = document.querySelector(".workspace"), compare = document.querySelector(".compare-panel");
  compare.classList.toggle("stacked", app.layout === "stacked");
  workspace.classList.toggle("queue-hidden", !app.queueVisible);
  workspace.classList.toggle("inspector-hidden", !app.inspectorVisible);
  el("layoutMode").value = app.layout;
  el("toggleQueue").textContent = t(app.queueVisible ? "hideQueue" : "showQueue");
  el("toggleInspector").textContent = t(app.inspectorVisible ? "hideInspector" : "showInspector");
  el("toggleQueue").setAttribute("aria-pressed", String(!app.queueVisible));
  el("toggleInspector").setAttribute("aria-pressed", String(!app.inspectorVisible));
  if (refit && app.state) requestAnimationFrame(fitView);
}

async function api(path, options = {}) {
  const response = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  const data = await response.json();
  if (!response.ok) {
    if (response.status === 409 && data.state) { app.state = data.state; renderAll(); }
    const error = new Error(data.error || `HTTP ${response.status}`); error.data = data; throw error;
  }
  return data;
}

function toast(message, error = false) {
  const box = el("toast"); box.textContent = message; box.style.background = error ? "#991b1b" : "#101828";
  box.classList.add("show"); clearTimeout(toast.timer); toast.timer = setTimeout(() => box.classList.remove("show"), 3200);
}

function pageInfo() { return app.state.session.pages.find(p => p.page_index === app.page); }
function nodes() { return app.state.graph.nodes; }
function edges() { return app.state.graph.edges; }
function nodeById(id) { return nodes().find(n => n.id === id); }
function reviewClass(status) { return status === "rejected" ? "rejected" : (status === "unreviewed" ? "" : "reviewed"); }

function setStageSize() {
  const page = pageInfo(); if (!page) return;
  for (const id of ["sourceStage", "inferenceStage"]) {
    const stage = el(id); stage.style.width = `${page.width * app.zoom}px`; stage.style.height = `${page.height * app.zoom}px`;
  }
  for (const id of ["sourceOverlay", "graphOverlay"]) el(id).setAttribute("viewBox", `0 0 ${page.width} ${page.height}`);
  el("zoomLabel").textContent = `${Math.round(app.zoom * 100)}%`;
}

function syncScroll(from, to) {
  if (app.syncing) return; app.syncing = true;
  const fx = from.scrollWidth - from.clientWidth, fy = from.scrollHeight - from.clientHeight;
  const tx = to.scrollWidth - to.clientWidth, ty = to.scrollHeight - to.clientHeight;
  to.scrollLeft = fx > 0 ? (from.scrollLeft / fx) * tx : 0;
  to.scrollTop = fy > 0 ? (from.scrollTop / fy) * ty : 0;
  requestAnimationFrame(() => { app.syncing = false; });
}

function svg(tag, attrs = {}) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
  Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, String(value)));
  return node;
}

function edgePage(edge) { return nodeById(edge.from_node)?.page_index ?? nodeById(edge.to_node)?.page_index ?? 0; }
function edgePoints(edge) {
  if (edge.polyline_global?.length) return edge.polyline_global;
  const a = nodeById(edge.from_node), b = nodeById(edge.to_node); if (!a || !b) return [];
  return [[a.bbox_global.x + a.bbox_global.w / 2, a.bbox_global.y + a.bbox_global.h / 2], [b.bbox_global.x + b.bbox_global.w / 2, b.bbox_global.y + b.bbox_global.h / 2]];
}

function renderOverlay() {
  const overlay = el("graphOverlay"); overlay.replaceChildren();
  edges().filter(edge => edgePage(edge) === app.page).forEach(edge => {
    const points = edgePoints(edge); if (!points.length) return;
    const poly = svg("polyline", { points: points.map(p => p.join(",")).join(" "), class: `graph-edge ${reviewClass(app.state.reviews.edges[edge.id])} ${app.selection?.id === edge.id ? "selected" : ""}` });
    poly.addEventListener("click", event => { event.stopPropagation(); select("edge", edge.id); }); overlay.append(poly);
    if (app.selection?.type === "edge" && app.selection.id === edge.id) addVertexHandles(overlay, edge, points, poly);
  });
  nodes().filter(node => node.page_index === app.page).forEach(node => {
    const b = node.bbox_global;
    const rect = svg("rect", { x: b.x, y: b.y, width: b.w, height: b.h, class: `graph-node ${reviewClass(app.state.reviews.nodes[node.id])} ${app.selection?.id === node.id ? "selected" : ""}` });
    rect.addEventListener("click", event => { event.stopPropagation(); select("node", node.id); });
    overlay.append(rect);
    const label = svg("text", { x: b.x + 3, y: Math.max(12, b.y - 4), class: "graph-label", "font-size": Math.max(11, Math.min(24, b.h * .18)) }); label.textContent = node.label || node.id; overlay.append(label);
    if (app.selection?.type === "node" && app.selection.id === node.id) {
      enableNodeDrag(rect, node, overlay);
      addNodeHandle(overlay, node, rect);
    }
  });
  overlay.onclick = () => { if (!app.drawMode) select(null, null); };
  renderSourceHighlight();
}

function pointerPoint(event, overlay) {
  const rect = overlay.getBoundingClientRect(), page = pageInfo();
  return [Math.max(0, Math.min(page.width, (event.clientX - rect.left) * page.width / rect.width)), Math.max(0, Math.min(page.height, (event.clientY - rect.top) * page.height / rect.height))];
}

function enableNodeDrag(rect, node, overlay) {
  rect.addEventListener("pointerdown", event => {
    event.stopPropagation(); rect.setPointerCapture(event.pointerId);
    const start = pointerPoint(event, overlay), original = {...node.bbox_global}; let moved = false;
    rect.onpointermove = move => {
      const point = pointerPoint(move, overlay), dx = point[0] - start[0], dy = point[1] - start[1];
      moved = moved || Math.abs(dx) + Math.abs(dy) > 2;
      node.bbox_global.x = Math.round(original.x + dx); node.bbox_global.y = Math.round(original.y + dy);
      rect.setAttribute("x", node.bbox_global.x); rect.setAttribute("y", node.bbox_global.y);
      renderSourceHighlight();
    };
    rect.onpointerup = async () => { rect.onpointermove = null; rect.onpointerup = null; if (moved) await submit("node", node.id, "modify", { bbox_global: roundBox(node.bbox_global) }); };
  });
}

function addNodeHandle(overlay, node, nodeRect) {
  const b = node.bbox_global, size = Math.max(10, 12 / app.zoom);
  const handle = svg("rect", { x: b.x + b.w - size / 2, y: b.y + b.h - size / 2, width: size, height: size, class: "handle" });
  handle.addEventListener("pointerdown", event => {
    event.stopPropagation(); handle.setPointerCapture(event.pointerId); const start = pointerPoint(event, overlay), original = {...b};
    handle.onpointermove = move => { const p = pointerPoint(move, overlay); node.bbox_global.w = Math.max(2, original.w + p[0] - start[0]); node.bbox_global.h = Math.max(2, original.h + p[1] - start[1]); nodeRect.setAttribute("width", node.bbox_global.w); nodeRect.setAttribute("height", node.bbox_global.h); handle.setAttribute("x", node.bbox_global.x + node.bbox_global.w - size / 2); handle.setAttribute("y", node.bbox_global.y + node.bbox_global.h - size / 2); renderSourceHighlight(); };
    handle.onpointerup = async () => { handle.onpointermove = null; await submit("node", node.id, "modify", { bbox_global: roundBox(node.bbox_global) }); };
  }); overlay.append(handle);
}

function addVertexHandles(overlay, edge, points, polyline) {
  points.forEach((point, index) => {
    const circle = svg("circle", { cx: point[0], cy: point[1], r: Math.max(6, 8 / app.zoom), class: "vertex" });
    circle.addEventListener("pointerdown", event => {
      event.stopPropagation(); circle.setPointerCapture(event.pointerId);
      circle.onpointermove = move => { const p = pointerPoint(move, overlay); points[index] = p; edge.polyline_global = points; circle.setAttribute("cx", p[0]); circle.setAttribute("cy", p[1]); polyline.setAttribute("points", points.map(item => item.join(",")).join(" ")); renderSourceHighlight(); };
      circle.onpointerup = async () => { circle.onpointermove = null; await submit("edge", edge.id, "modify", { polyline_global: points.map(p => p.map(Math.round)) }); };
    }); overlay.append(circle);
  });
}

function roundBox(b) { return { x: Math.round(b.x), y: Math.round(b.y), w: Math.max(1, Math.round(b.w)), h: Math.max(1, Math.round(b.h)) }; }

function renderSourceHighlight() {
  const overlay = el("sourceOverlay"); overlay.replaceChildren(); if (!app.selection) return;
  const page = pageInfo(), group = svg("g", { transform: page.rotation_deg ? `rotate(${-page.rotation_deg} ${page.width / 2} ${page.height / 2})` : "" });
  if (app.selection.type === "node") {
    const node = nodeById(app.selection.id); if (!node || node.page_index !== app.page) return;
    const b = node.bbox_global; group.append(svg("rect", { x: b.x, y: b.y, width: b.w, height: b.h, class: "source-highlight" }));
  } else if (app.selection.type === "edge") {
    const edge = edges().find(item => item.id === app.selection.id); if (!edge || edgePage(edge) !== app.page) return;
    group.append(svg("polyline", { points: edgePoints(edge).map(p => p.join(",")).join(" "), class: "source-highlight", fill: "none" }));
  }
  overlay.append(group);
}

function renderQueue() {
  const filter = el("queueFilter").value, type = el("queueType").value, rows = [...app.state.queue];
  Object.entries(app.state.reviews.conflicts).forEach(([id, item]) => rows.push({ target_type: "conflict", target_id: id, page_index: null, label: item.conflict.type || id, status: item.status, tier: 0, reasons: ["graph conflict"] }));
  const visible = rows.filter(row => (filter === "all" || row.status === "unreviewed") && (type === "all" || row.target_type === type));
  const box = el("queue"); box.replaceChildren();
  visible.forEach(row => {
    const button = document.createElement("button"); button.className = `queue-item ${app.selection?.id === row.target_id ? "selected" : ""}`;
    const typeLabel = t(row.target_type === "node" ? "entity" : row.target_type === "edge" ? "connection" : "conflict");
    const pageLabel = row.page_index == null ? "" : ` · ${t("pageShort", {page: row.page_index + 1})}`;
    const rowLabel = row.target_type === "conflict" ? displayValue(row.label) : row.label;
    button.innerHTML = `<span class="kind"><i class="status-dot ${row.status}"></i>${escapeHtml(typeLabel)}${escapeHtml(pageLabel)}</span><span class="label">${escapeHtml(rowLabel)}</span><span class="reason">${escapeHtml(row.reasons.map(translateReason).join(" · "))}</span>`;
    button.onclick = () => { if (row.page_index != null) changePage(row.page_index); select(row.target_type, row.target_id); }; box.append(button);
  });
  if (!visible.length) { const empty = document.createElement("div"); empty.className = "inspector empty"; empty.textContent = t("noMatches"); box.append(empty); }
}

function escapeHtml(value) { const div = document.createElement("div"); div.textContent = String(value ?? ""); return div.innerHTML; }

function inputField(label, id, value, type = "text") { return `<label class="field">${label}<input id="${id}" type="${type}" value="${escapeHtml(value)}"></label>`; }
function selectField(label, id, value, choices) { return `<label class="field">${label}<select id="${id}">${choices.map(c => `<option value="${escapeHtml(c)}" ${c === value ? "selected" : ""}>${escapeHtml(displayValue(c))}</option>`).join("")}</select></label>`; }

function renderInspector() {
  const box = el("inspector");
  if (!app.selection) { box.className = "inspector empty"; box.textContent = t("selectItem"); return; }
  box.className = "inspector"; const {type, id} = app.selection;
  if (type === "node") {
    const node = nodeById(id); if (!node) return select(null, null); const b = node.bbox_global;
    box.innerHTML = `<h3>${escapeHtml(node.label || node.id)}</h3><div class="meta">${escapeHtml(node.id)} · ${t("modelConfidence")} ${escapeHtml(displayValue(node.confidence))} · ${t("review")} ${escapeHtml(displayValue(app.state.reviews.nodes[id]))}</div>
      ${inputField(t("label"), "nodeLabel", node.label)}${selectField(t("kind"), "nodeKind", node.kind, app.state.taxonomy.kinds)}
      ${selectField(t("equipmentClass"), "nodeEquipmentClass", (node.attributes || {}).equipment_class || "", ["", ...app.state.taxonomy.equipment_classes])}
      ${selectField(t("valveType"), "nodeValveType", (node.attributes || {}).valve_type || "", ["", ...app.state.taxonomy.valve_types])}
      ${selectField(t("instrumentFunction"), "nodeInstrumentFunction", (node.attributes || {}).instrument_function || "", ["", ...app.state.taxonomy.instrument_functions])}
      <div class="geometry">${inputField("X", "nodeX", b.x, "number")}${inputField("Y", "nodeY", b.y, "number")}${inputField("W", "nodeW", b.w, "number")}${inputField("H", "nodeH", b.h, "number")}</div>
      <label class="field">${t("attributesJson")}<textarea id="nodeAttrs">${escapeHtml(JSON.stringify(node.attributes || {}, null, 2))}</textarea></label>
      <div class="actions"><button id="saveNode">${t("saveChanges")}</button><button id="approveNode" class="primary">${t("approve")}</button><button id="rejectNode" class="danger">${t("reject")}</button></div>`;
    el("saveNode").onclick = async () => { try { const attrs=JSON.parse(el("nodeAttrs").value); const assign=(key,value)=>value?attrs[key]=value:delete attrs[key]; assign("equipment_class",el("nodeEquipmentClass").value); assign("valve_type",el("nodeValveType").value); assign("instrument_function",el("nodeInstrumentFunction").value); await submit("node", id, "modify", { label: el("nodeLabel").value, kind: el("nodeKind").value, bbox_global: { x:+el("nodeX").value, y:+el("nodeY").value, w:+el("nodeW").value, h:+el("nodeH").value }, attributes: attrs }); } catch (error) { toast(error.message, true); } };
    el("approveNode").onclick = () => submit("node", id, "approve"); el("rejectNode").onclick = () => submit("node", id, "reject", {}, prompt(t("rejectReason")) || "");
  } else if (type === "edge") {
    const edge = edges().find(item => item.id === id); if (!edge) return select(null, null);
    const nodeOptions = nodes().filter(n => app.state.reviews.nodes[n.id] !== "rejected").map(n => [n.id, `${n.label || n.id} (${n.id})`]);
    const options = value => nodeOptions.map(([id, label]) => `<option value="${id}" ${id === value ? "selected" : ""}>${escapeHtml(label)}</option>`).join("");
    box.innerHTML = `<h3>${escapeHtml((edge.attributes || {}).line_id || edge.id)}</h3><div class="meta">${escapeHtml(edge.id)} · ${t("modelConfidence")} ${escapeHtml(displayValue(edge.confidence))} · ${t("review")} ${escapeHtml(displayValue(app.state.reviews.edges[id]))}</div>
      <label class="field">${t("from")}<select id="edgeFrom">${options(edge.from_node)}</select></label><label class="field">${t("to")}<select id="edgeTo">${options(edge.to_node)}</select></label>
      ${selectField(t("lineType"), "edgeType", edge.line_type || "other", app.state.taxonomy.line_types)}
      <label class="field">${t("polylineJson")}<textarea id="edgePoints">${escapeHtml(JSON.stringify(edge.polyline_global || [], null, 2))}</textarea></label>
      <label class="field">${t("attributesJson")}<textarea id="edgeAttrs">${escapeHtml(JSON.stringify(edge.attributes || {}, null, 2))}</textarea></label>
      <div class="actions"><button id="saveEdge">${t("saveChanges")}</button><button id="approveEdge" class="primary">${t("approve")}</button><button id="rejectEdge" class="danger">${t("reject")}</button></div>`;
    el("saveEdge").onclick = async () => { try { await submit("edge", id, "modify", { from_node: el("edgeFrom").value, to_node: el("edgeTo").value, line_type: el("edgeType").value, polyline_global: JSON.parse(el("edgePoints").value), attributes: JSON.parse(el("edgeAttrs").value) }); } catch (error) { toast(error.message, true); } };
    el("approveEdge").onclick = () => submit("edge", id, "approve"); el("rejectEdge").onclick = () => submit("edge", id, "reject", {}, prompt(t("rejectReason")) || "");
  } else if (type === "conflict") {
    const item = app.state.reviews.conflicts[id]; if (!item) return select(null, null);
    box.innerHTML = `<h3>${escapeHtml(item.conflict.type ? displayValue(item.conflict.type) : t("graphConflict"))}</h3><div class="meta">${escapeHtml(id)} · ${t("review")} ${escapeHtml(displayValue(item.status))}</div><pre class="conflict-json">${escapeHtml(JSON.stringify(item.conflict, null, 2))}</pre><div class="actions"><button id="resolveConflict" class="primary">${t("resolved")}</button><button id="waiveConflict">${t("waiveReason")}</button></div>`;
    el("resolveConflict").onclick = () => submit("conflict", id, "resolve", {}, prompt(t("resolveReason")) || "");
    el("waiveConflict").onclick = () => { const reason = prompt(t("conflictWaiveReason")); if (reason) submit("conflict", id, "waive", {}, reason); };
  }
}

function select(type, id) { app.selection = type ? {type, id} : null; renderOverlay(); renderQueue(); renderInspector(); }

async function submit(target_type, target_id, operation, after = {}, reason = "") {
  try {
    const result = await api("/api/action", { method: "POST", body: JSON.stringify({ expected_revision: app.state.revision, target_type, target_id, operation, after, reason }) });
    app.state = result.state; if (result.event.target_id) app.selection = {type: result.event.target_type, id: result.event.target_id}; renderAll(); toast(t("actionSaved", {operation: displayValue(operation)})); return result;
  } catch (error) { toast(error.message, true); throw error; }
}

function changePage(index, preserveSelection = false) {
  const count = app.state.session.pages.length; app.page = Math.max(0, Math.min(count - 1, index)); if (!preserveSelection) app.selection = null;
  const page = pageInfo(); el("sourceImage").src = `/api/pages/${app.page}/source`; el("inferenceImage").src = `/api/pages/${app.page}/inference`;
  el("pageLabel").textContent = t("pageCount", {current: app.page + 1, count}); el("pageRole").value = app.state.reviews.pages[String(app.page)]?.role || "pid";
  setStageSize(); renderOverlay(); renderInspector(); renderQueue();
}

function renderProgress() {
  const c = app.state.completion;
  const remaining = c.unreviewed_pages.length + c.unreviewed_nodes.length + c.unreviewed_edges.length + c.unresolved_conflicts.length;
  el("progressBadge").textContent = remaining ? t("remaining", {count: remaining}) : t("readyExport");
  el("finishButton").disabled = !c.complete;
  const warnings = app.state.warnings || []; el("warningBox").classList.toggle("hidden", !warnings.length); el("warningBox").textContent = warnings.map(translateWarning).join("\n");
}

function renderAll() { renderProgress(); changePage(app.page, true); }

function fitView() {
  const page=pageInfo(), viewport=el("inferenceViewport");
  app.zoom=Math.max(.05,Math.min(1,(viewport.clientWidth-28)/page.width,(viewport.clientHeight-28)/page.height));
  setStageSize();
}

function beginDrawNode() {
  app.drawMode = true; toast(t("drawInstruction")); const overlay = el("graphOverlay");
  overlay.onpointerdown = event => {
    if (!app.drawMode || event.target !== overlay) return; const start = pointerPoint(event, overlay), draft = svg("rect", { x:start[0], y:start[1], width:1, height:1, class:"graph-node selected" }); overlay.append(draft); overlay.setPointerCapture(event.pointerId);
    overlay.onpointermove = move => { const p = pointerPoint(move, overlay); draft.setAttribute("x", Math.min(start[0], p[0])); draft.setAttribute("y", Math.min(start[1], p[1])); draft.setAttribute("width", Math.abs(p[0]-start[0])); draft.setAttribute("height", Math.abs(p[1]-start[1])); };
    overlay.onpointerup = async move => { overlay.onpointermove = null; overlay.onpointerup = null; overlay.onpointerdown = null; app.drawMode = false; const p = pointerPoint(move, overlay), box = {x:Math.round(Math.min(start[0],p[0])), y:Math.round(Math.min(start[1],p[1])), w:Math.max(2,Math.round(Math.abs(p[0]-start[0]))), h:Math.max(2,Math.round(Math.abs(p[1]-start[1])))}; await submit("node", "", "add", {kind:"equipment",label:t("unlabelled"),bbox_global:box,page_index:app.page,attributes:{review_added:true},confidence:"medium",alternate_readings:[],source_annotation_ids:[]}); };
  };
}

async function addEdge() {
  const active = nodes().filter(n => app.state.reviews.nodes[n.id] !== "rejected"); if (active.length < 2) return toast(t("twoEntitiesRequired"), true);
  const from = prompt(t("fromEntityPrompt")); if (!from) return; const to = prompt(t("toEntityPrompt")); if (!to) return;
  const resolve = value => active.find(n => n.id === value || n.label === value)?.id; const fromId = resolve(from), toId = resolve(to); if (!fromId || !toId) return toast(t("unresolvedEntity"), true);
  const a=nodeById(fromId), b=nodeById(toId), points=[[Math.round(a.bbox_global.x+a.bbox_global.w/2),Math.round(a.bbox_global.y+a.bbox_global.h/2)],[Math.round(b.bbox_global.x+b.bbox_global.w/2),Math.round(b.bbox_global.y+b.bbox_global.h/2)]];
  await submit("edge", "", "add", {from_node:fromId,to_node:toId,line_type:"process",polyline_global:points,cross_sheet:a.page_index!==b.page_index,confidence:"medium",source_annotation_ids:[],attributes:{review_added:true}});
}

function populatePageRoles() {
  const selected = el("pageRole").value;
  el("pageRole").replaceChildren();
  app.state.taxonomy.page_roles.forEach(role => {
    const option = document.createElement("option"); option.value = role; option.textContent = displayValue(role); el("pageRole").append(option);
  });
  el("pageRole").value = selected || app.state.reviews.pages[String(app.page)]?.role || "pid";
}

async function init() {
  applyLanguage();
  applyWorkspaceLayout(false);
  app.state = await api("/api/state");
  populatePageRoles();
  el("languageSwitch").onchange = () => {
    app.lang = el("languageSwitch").value;
    storeSetting("diagex.review.language", app.lang);
    applyLanguage(); populatePageRoles(); applyWorkspaceLayout(false); renderAll();
  };
  el("layoutMode").onchange = () => { app.layout = el("layoutMode").value; storeSetting("diagex.review.layout", app.layout); applyWorkspaceLayout(); };
  el("toggleQueue").onclick = () => { app.queueVisible = !app.queueVisible; storeSetting("diagex.review.queueVisible", app.queueVisible); applyWorkspaceLayout(); };
  el("toggleInspector").onclick = () => { app.inspectorVisible = !app.inspectorVisible; storeSetting("diagex.review.inspectorVisible", app.inspectorVisible); applyWorkspaceLayout(); };
  el("sourceViewport").onscroll = () => syncScroll(el("sourceViewport"), el("inferenceViewport")); el("inferenceViewport").onscroll = () => syncScroll(el("inferenceViewport"), el("sourceViewport"));
  el("prevPage").onclick=()=>changePage(app.page-1); el("nextPage").onclick=()=>changePage(app.page+1);
  el("zoomIn").onclick=()=>{app.zoom=Math.min(2.5,app.zoom+.15);setStageSize();}; el("zoomOut").onclick=()=>{app.zoom=Math.max(.05,app.zoom-.15);setStageSize();}; el("fitView").onclick=fitView;
  el("backgroundMode").onchange=()=>{ const img=el("inferenceImage"), mode=el("backgroundMode").value; img.style.opacity=mode==="none"?0:(mode==="dim"?.2:1); };
  el("approvePage").onclick=()=>submit("page",String(app.page),"approve",{role:el("pageRole").value}); el("waivePage").onclick=()=>{const reason=prompt(t("pageWaiveReason"));if(reason)submit("page",String(app.page),"waive",{role:el("pageRole").value},reason);};
  el("queueFilter").onchange=renderQueue; el("queueType").onchange=renderQueue; el("addNode").onclick=beginDrawNode; el("addEdge").onclick=addEdge;
  el("undoButton").onclick=()=>submit("", "", "undo");
  el("finishButton").onclick=async()=>{try{const result=await api("/api/finish",{method:"POST",body:JSON.stringify({expected_revision:app.state.revision})});app.state=result.state;renderAll();toast(t("exportSuccess"));}catch(error){toast(error.message,true);}};
  changePage(0); fitView(); renderProgress();
}

init().catch(error => toast(t("loadFailed", {message: error.message}), true));
