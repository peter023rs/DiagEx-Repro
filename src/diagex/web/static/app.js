const $ = (id) => document.getElementById(id);

const I18N = {
  "en": {
    "symbolLibrary": "Symbol library",
    "referenceStandard": "Symbol reference standard",
    "projectOnly": "Project legend only",
    "referenceHint": "Adds starter definitions and imported reference guides. Your drawing's legend takes priority. IEC catalog entries have no graphics and are not used for detection.",
    "subtitle": "P&ID symbol detection workbench",
    "connecting": "Connecting",
    "online": "Local server online",
    "localWorkbench": "LOCAL WORKBENCH",
    "title": "Find symbols in your P&ID",
    "intro": "Configure models, upload a drawing, and inspect source-aligned symbol results.",
    "credentialsStayLocal": "Credentials are not saved",
    "credentialsDetail": "Keys are kept in this server process, sent only to the selected API endpoint, and never saved to .env or run artifacts.",
    "configure": "Configure detection",
    "configureHint": "Choose the provider and models used for this run.",
    "provider": "Provider",
    "providerRouting": "OpenRouter provider routing",
    "providerOrder": "Preferred providers, in order",
    "providerIgnore": "Excluded providers",
    "providerFallbacks": "Allow other providers as fallbacks",
    "routingHint": "Optional comma-separated OpenRouter provider slugs. Providers must serve the selected model. Leave blank for automatic routing.",
    "baseUrl": "API endpoint",
    "apiKey": "API key",
    "apiKeyPlaceholder": "Leave blank to use the configured environment key",
    "show": "Show",
    "hide": "Hide",
    "environmentKeyAvailable": "A configured key is available. Leave this field blank to use it.",
    "keyRequired": "No configured key found. Enter one for this run.",
    "visionModel": "Vision model",
    "visionHint": "Used for raw symbol detection. Enable reasoning below for difficult symbols.",
    "reasoningModel": "Reinspection model",
    "reasoningModelHint": "Used for bounded reinspection of difficult symbols.",
    "reasoningHint": "Symbol detection starts with a fast pass. Enabled adds one limited check for uncertain or rejected symbols and ambiguous equipment bodies, using enlarged details.",
    "reasoning": "Reasoning",
    "automatic": "Automatic",
    "enabled": "Enabled",
    "disabled": "Disabled",
    "effort": "Reasoning effort",
    "low": "Low",
    "medium": "Medium",
    "high": "High",
    "xhigh": "Extra high",
    "chooseDrawing": "Choose the drawing",
    "chooseDrawingHint": "PDF is recommended; vector PDFs give the strongest line evidence.",
    "dropDrawing": "Drop a P&ID here",
    "orBrowse": "or click to choose a file",
    "replace": "Replace",
    "artifactReuse": "Artifact reuse",
    "reuseArtifacts": "Resume compatible artifacts",
    "reuseHint": "Continue an interrupted matching run when possible.",
    "startFresh": "Start a brand-new run",
    "freshHint": "Bypass compatible machine caches; preserve previous results.",
    "startExtraction": "Detect symbols",
    "queued": "Queued",
    "extractionProgress": "Detection progress",
    "elapsed": "Elapsed",
    "liveLog": "Live detection log",
    "autoScroll": "Auto-scroll",
    "copy": "Copy",
    "extractionFinished": "Detection finished",
    "runDirectory": "Run directory",
    "recentRuns": "Open an existing run",
    "recentRunsHint": "Reopen saved detection results without model calls.",
    "refreshRuns": "Refresh runs",
    "filterRuns": "Find a run",
    "filterRunsPlaceholder": "Drawing, run ID, or model",
    "attachSource": "Attach original drawing",
    "sourceVerified": "Source verified",
    "sourceFound": "Source found",
    "sourceNeeded": "Source PDF needed",
    "sourceUploading": "Uploading source P&ID…",
    "uploading": "Uploading drawing…",
    "uploaded": "Drawing uploaded",
    "running": "Running",
    "succeeded": "Finished",
    "failed": "Failed",
    "quality": "Quality",
    "tokens": "Tokens",
    "copied": "Log copied",
    "sourceUnavailable": "Original source unavailable",
    "detectSymbols": "Detect symbols",
    "detectHint": "Machine observations may repeat across overlapping crops. Candidates remain separate from detections.",
    "viewResults": "View results",
    "viewResults": "View results",
    "observations": "Symbol observations",
    "candidates": "Native candidates",
    "legendEntries": "Legend entries",
    "unsupported": "Graph-only run: unsupported"
  },
  "zh-CN": {
    "symbolLibrary": "符号库",
    "referenceStandard": "符号参考标准",
    "projectOnly": "仅使用项目图例",
    "referenceHint": "添加初始定义和已导入的参考手册，当前图纸图例优先。IEC 目录条目暂无图形，不用于检测。",
    "subtitle": "P&ID 符号检测工作台",
    "connecting": "正在连接",
    "online": "本地服务已连接",
    "localWorkbench": "本地工作台",
    "title": "发现 P&ID 中的符号",
    "intro": "配置模型、上传图纸，查看与原图对齐的符号检测结果。",
    "credentialsStayLocal": "凭证不会被保存",
    "credentialsDetail": "密钥仅保留在当前服务进程中并发送至所选 API 地址，不会写入 .env 或运行产物。",
    "configure": "配置检测",
    "configureHint": "选择本次运行使用的服务商和模型。",
    "provider": "服务商",
    "baseUrl": "API 地址",
    "apiKey": "API 密钥",
    "apiKeyPlaceholder": "留空则使用当前环境中已配置的密钥",
    "show": "显示",
    "hide": "隐藏",
    "environmentKeyAvailable": "已检测到配置密钥；留空即可使用。",
    "keyRequired": "没有检测到配置密钥，请输入本次运行使用的密钥。",
    "visionModel": "视觉模型",
    "visionHint": "用于原始符号识别；可在下方启用推理，帮助识别困难符号。",
    "reasoningModel": "复检模型",
    "reasoningModelHint": "用于对困难符号进行有界复检。",
    "reasoningHint": "符号识别先进行快速检测；启用推理后，使用放大细节对不确定或被排除的符号及易混淆设备追加一次限时检查。",
    "reasoning": "推理模式",
    "automatic": "自动",
    "enabled": "启用",
    "disabled": "禁用",
    "effort": "推理强度",
    "low": "低",
    "medium": "中",
    "high": "高",
    "xhigh": "超高",
    "chooseDrawing": "选择图纸",
    "chooseDrawingHint": "建议使用 PDF；矢量 PDF 可提供更可靠的线条证据。",
    "dropDrawing": "将 P&ID 拖到这里",
    "orBrowse": "或点击选择文件",
    "replace": "更换",
    "artifactReuse": "产物复用",
    "reuseArtifacts": "复用兼容产物",
    "reuseHint": "如存在匹配的中断任务，则从检查点继续。",
    "startFresh": "开始全新运行",
    "freshHint": "跳过机器缓存，保留之前的结果。",
    "startExtraction": "检测符号",
    "queued": "排队中",
    "extractionProgress": "检测进度",
    "elapsed": "已用时间",
    "liveLog": "实时检测日志",
    "autoScroll": "自动滚动",
    "copy": "复制",
    "extractionFinished": "检测完成",
    "runDirectory": "运行目录",
    "recentRuns": "打开已有运行",
    "recentRunsHint": "重新打开已保存的检测结果，不调用模型。",
    "refreshRuns": "刷新运行列表",
    "filterRuns": "查找运行",
    "filterRunsPlaceholder": "图纸、运行 ID 或模型",
    "attachSource": "关联原始图纸",
    "sourceVerified": "原图已校验",
    "sourceFound": "已找到原图",
    "sourceNeeded": "需要关联原始图纸",
    "sourceUploading": "正在上传原始 P&ID…",
    "uploading": "正在上传图纸…",
    "uploaded": "图纸上传完成",
    "running": "运行中",
    "succeeded": "已完成",
    "failed": "失败",
    "quality": "质量状态",
    "tokens": "令牌",
    "copied": "日志已复制",
    "sourceUnavailable": "原始图纸不可用",
    "detectSymbols": "检测符号",
    "detectHint": "重叠裁剪可能重复观测同一个符号。候选与检测结果分别显示。",
    "viewResults": "查看结果",
    "viewResults": "查看结果",
    "observations": "符号观测",
    "candidates": "原生候选",
    "legendEntries": "图例条目",
    "unsupported": "仅含连接图的运行：不支持"
  }
};

Object.assign(I18N.en, {complete:"Complete", partial:"Partial", paused:"Paused", estimatedCost:"Estimated cost (USD)"});
Object.assign(I18N["zh-CN"], {complete:"完成", partial:"部分完成", paused:"暂停", estimatedCost:"估算费用（美元）"});
Object.assign(I18N.en, {
  modelPreset: "Vision model preset", openWeightPreset: "Open-weight models", customModels: "Custom models",
  glmReasoning: "GLM-5.3 requires reasoning; requests keep it enabled regardless of the setting below.",
  qwenReasoning: "Qwen3-VL Instruct does not accept reasoning settings; they are omitted for this model.",
  modelPresetHint: "Presets fill in the fields below. You can change either model at any time.",
  modelPlaceholder: "Search models or enter provider/model-id", sameVisionModel: "Same as vision model when blank",
  visionHint: "Choose an image-capable model with tool support, or paste its OpenRouter model ID.",
  reasoningModelHint: "Optional model for difficult symbols. Leave blank to use the vision model.",
  refreshModels: "Refresh OpenRouter models", browseModels: "Browse models ↗",
  modelsLoading: "Loading OpenRouter models…", modelsLoaded: "{count} models with image input and tool support. Type in either model field to search.",
  modelsUnavailable: "Model list unavailable. You can still paste an OpenRouter model ID.",
});
Object.assign(I18N["zh-CN"], {
  modelPreset: "视觉模型预设", openWeightPreset: "开放权重模型", customModels: "自定义模型",
  glmReasoning: "GLM-5.3 必须启用推理；下方设置不会关闭该模型的推理。",
  qwenReasoning: "Qwen3-VL Instruct 不支持推理参数；该模型的请求会省略这些设置。",
  providerRouting: "OpenRouter 服务商路由",
  providerOrder: "优先服务商（按顺序）",
  providerIgnore: "排除的服务商",
  providerFallbacks: "允许回退到其他服务商",
  routingHint: "可选，用英文逗号分隔 OpenRouter 服务商标识。服务商须提供所选模型。留空使用自动路由。",
  modelPresetHint: "预设会填入下方配置，您可以随时修改模型。",
  modelPlaceholder: "搜索模型或输入 provider/model-id", sameVisionModel: "留空使用视觉模型",
  visionHint: "选择支持图像输入和工具调用的模型，或粘贴 OpenRouter 模型 ID。",
  reasoningModelHint: "用于困难符号的可选复检模型。留空使用视觉模型。",
  refreshModels: "刷新 OpenRouter 模型", browseModels: "浏览模型 ↗",
  modelsLoading: "正在加载 OpenRouter 模型…", modelsLoaded: "{count} 个模型支持图像输入和工具调用。在模型输入框中搜索。",
  modelsUnavailable: "暂时无法加载模型列表。您仍可粘贴 OpenRouter 模型 ID。",
});
const state = {
  language: localStorage.getItem("diagex.web.language") || "en",
  config: null,
  upload: null,
  job: null,
  logCursor: 0,
  pollTimer: null,
  elapsedTimer: null,
  logLines: [],
  connected: false,
  pendingSourceRun: null,
  modelCatalog: null,
  catalogStatus: "idle",
};

const providerDefaults = {
  openrouter: "https://openrouter.ai/api",
  kimi: "https://api.kimi.com/coding/v1",
  anthropic: "",
  azure: "",
};

function t(key) { return (I18N[state.language] || I18N.en)[key] || I18N.en[key] || key; }

function applyLanguage() {
  document.documentElement.lang = state.language;
  $("languageSwitch").value = state.language;
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    const value = t(node.dataset.i18n);
    if (value) node.textContent = value;
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => {
    node.placeholder = t(node.dataset.i18nPlaceholder);
  });
  updateKeyStatus();
  renderModelCatalog();
  updateModelConstraintHint();
  if (state.connected) $("serverStatus").querySelector("span").textContent = t("online");
  if (state.job) renderJob(state.job);
  renderRecentRuns(window.__recentRuns || []);
}

function showToast(message) {
  const toast = $("toast");
  toast.textContent = message;
  toast.classList.add("show");
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => toast.classList.remove("show"), 2600);
}

async function api(path, options = {}) {
  const response = await fetch(path, options);
  const type = response.headers.get("content-type") || "";
  const payload = type.includes("json") ? await response.json() : { error: await response.text() };
  if (!response.ok) throw new Error(payload.error || `Request failed (${response.status})`);
  return payload;
}

function humanBytes(value) {
  if (value < 1024) return `${value} B`;
  if (value < 1024 ** 2) return `${(value / 1024).toFixed(1)} KiB`;
  return `${(value / 1024 ** 2).toFixed(1)} MiB`;
}

function formatTime(seconds) {
  const total = Math.max(0, Math.floor(seconds || 0));
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const secs = total % 60;
  return hours ? `${hours}:${String(minutes).padStart(2, "0")}:${String(secs).padStart(2, "0")}` : `${String(minutes).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}

function formatTokens(tokens) { return tokens >= 1e6 ? `${(tokens / 1e6).toFixed(3)}M` : `${Math.round(tokens / 1000)}k`; }

function updateKeyStatus() {
  if (!state.config) return;
  const provider = $("provider").value;
  const available = Boolean(state.config.configured_keys?.[provider]);
  $("keyStatus").textContent = available ? t("environmentKeyAvailable") : t("keyRequired");
  $("keyStatus").style.color = available ? "#138a58" : "#b76808";
}

function updateProvider() {
  const provider = $("provider").value;
  const field = $("baseUrlField");
  field.classList.toggle("hidden", provider === "anthropic");
  const current = $("baseUrl").value;
  if (!current || Object.values(providerDefaults).includes(current)) $("baseUrl").value = providerDefaults[provider];
  updateKeyStatus();
  renderModelCatalog();
  if (provider === "openrouter" && state.catalogStatus === "idle") loadOpenRouterModels();
}

function renderModelCatalog() {
  const openrouter = $("provider").value === "openrouter";
  $("openrouterModels").classList.toggle("hidden", !openrouter);
  $("openrouterRouting").classList.toggle("hidden", !openrouter);
  $("modelSuggestions").replaceChildren(...(openrouter ? state.modelCatalog || [] : []).map(model => {
    const option = document.createElement("option");
    option.value = model.id;
    option.label = model.name || model.id;
    return option;
  }));
  $("refreshModels").disabled = state.catalogStatus === "loading";
  const key = state.catalogStatus === "loaded" ? "modelsLoaded" : state.catalogStatus === "error" ? "modelsUnavailable" : "modelsLoading";
  $("modelCatalogStatus").textContent = t(key).replace("{count}", state.modelCatalog?.length || 0);
}

async function loadOpenRouterModels() {
  if (state.catalogStatus === "loading") return;
  state.catalogStatus = "loading";
  renderModelCatalog();
  try {
    // Public catalog request: no API key or drawing data is sent.
    const response = await fetch("https://openrouter.ai/api/v1/models", {
      credentials: "omit", signal: AbortSignal.timeout(12000),
    });
    if (!response.ok) throw new Error("Model catalog unavailable");
    const payload = await response.json();
    if (!Array.isArray(payload.data)) throw new Error("Invalid model catalog");
    state.modelCatalog = payload.data.filter(model =>
      typeof model?.id === "string" && model.architecture?.input_modalities?.includes("image") &&
      model.supported_parameters?.includes("tools")
    ).sort((a, b) => a.id.localeCompare(b.id));
    state.catalogStatus = "loaded";
  } catch (_error) {
    state.catalogStatus = "error";
  }
  renderModelCatalog();
}

async function uploadDrawing(file) {
  const suffix = file.name.split(".").pop().toLowerCase();
  if (!["pdf", "png", "jpg", "jpeg", "tif", "tiff", "bmp"].includes(suffix)) {
    throw new Error("Upload a PDF or supported image file");
  }
  return api(`/api/uploads?filename=${encodeURIComponent(file.name)}`, {
    method: "POST", headers: { "Content-Type": file.type || "application/octet-stream" }, body: file,
  });
}

async function uploadFile(file) {
  $("uploadProgress").classList.remove("hidden");
  $("dropZone").classList.add("hidden");
  $("startButton").disabled = true;
  try {
    const payload = await uploadDrawing(file);
    state.upload = payload.upload;
    $("fileName").textContent = state.upload.filename;
    $("fileSize").textContent = humanBytes(state.upload.size);
    $("fileSummary").classList.remove("hidden");
    $("startButton").disabled = false;
    showToast(t("uploaded"));
  } finally {
    $("uploadProgress").classList.add("hidden");
  }
}

function extractionPayload() {
  return {
    upload_id: state.upload?.id,
    symbol_standard: $("symbolStandard").value,
    model_policy: $("modelPolicy").value,
    provider: $("provider").value,
    api_key: $("apiKey").value,
    base_url: $("baseUrl").value.trim(),
    vision_model: $("visionModel").value.trim(),
    reasoning_model: $("reasoningModel").value.trim(),
    reasoning_mode: $("reasoningMode").value,
    effort: $("effort").value,
    engine: "evidence-v2",
    fresh: document.querySelector('input[name="runMode"]:checked').value === "fresh",
    ...($("provider").value === "openrouter" ? {
      openrouter_provider_order: $("providerOrder").value.split(",").map(s => s.trim()).filter(Boolean),
      openrouter_provider_ignore: $("providerIgnore").value.split(",").map(s => s.trim()).filter(Boolean),
      openrouter_allow_fallbacks: $("providerFallbacks").value === "true",
    } : {}),
  };
}

async function startExtraction() {
  $("formError").classList.add("hidden");
  $("startButton").disabled = true;
  try {
    const payload = await api("/api/extractions", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({...extractionPayload(), stop_after:"detection"}),
    });
    $("apiKey").value = "";
    state.job = payload.job;
    state.logCursor = 0;
    state.logLines = [];
    $("jobLog").textContent = "";
    $("runSection").classList.remove("hidden");
    $("resultSection").classList.add("hidden");
    $("runSection").scrollIntoView({ behavior: "smooth", block: "start" });
    renderJob(state.job);
    schedulePoll(250);
    startElapsedClock();
  } catch (error) {
    $("formError").textContent = error.message;
    $("formError").classList.remove("hidden");
    $("startButton").disabled = false;
  }
}

function schedulePoll(delay = 1200) {
  clearTimeout(state.pollTimer);
  state.pollTimer = setTimeout(pollJob, delay);
}

async function pollJob() {
  if (!state.job) return;
  try {
    const job = await api(`/api/jobs/${encodeURIComponent(state.job.id)}?after=${state.logCursor}`);
    state.job = job;
    state.logCursor = job.log_cursor;
    for (const entry of job.logs || []) state.logLines.push(entry.text);
    if (state.logLines.length > 10000) state.logLines = state.logLines.slice(-10000);
    $("jobLog").textContent = state.logLines.join("\n");
    if ($("autoScroll").checked) $("jobLog").scrollTop = $("jobLog").scrollHeight;
    renderJob(job);
    if (!["succeeded", "failed", "paused"].includes(job.status)) schedulePoll();
    else {
      clearInterval(state.elapsedTimer);
      $("startButton").disabled = false;
      loadRecentRuns();
    }
  } catch (error) {
    $("jobError").textContent = error.message;
    $("jobError").classList.remove("hidden");
    schedulePoll(3000);
  }
}

function renderJob(job) {
  const label = job.status === "paused" ? (state.language === "zh-CN" ? "已暂停 · 可续跑" : "Paused · resumable") : (t(job.status) || job.status);
  $("jobState").textContent = label;
  $("jobState").className = `pill ${job.status === "failed" ? "error" : job.status === "succeeded" ? "ok" : job.status === "paused" ? "partial" : "running"}`;
  $("jobSubtitle").textContent = `${job.filename} · ${job.settings.vision_model} → ${job.settings.reasoning_model}`;
  $("jobError").classList.toggle("hidden", !job.error);
  $("jobError").textContent = job.error || "";
  $("activityBar").className = `activity-bar ${["succeeded", "paused"].includes(job.status) ? "done" : job.status === "failed" ? "failed" : ""}`;
  if (["succeeded", "paused"].includes(job.status) && job.result) renderResult(job);
}

function startElapsedClock() {
  clearInterval(state.elapsedTimer);
  state.elapsedTimer = setInterval(() => {
    if (!state.job?.started_at) return;
    const start = Date.parse(state.job.started_at);
    const end = state.job.finished_at ? Date.parse(state.job.finished_at) : Date.now();
    $("elapsedTime").textContent = formatTime((end - start) / 1000);
  }, 1000);
}

function metric(label, value) { return `<div class="metric"><strong>${value}</strong><span>${label}</span></div>`; }

function renderResult(job) {
  const result = job.result;
  const stats = result.stats || {};
  const quality = result.quality_status || "unknown";
  $("resultSection").classList.remove("hidden");
  $("qualityBadge").textContent = `${t("quality")}: ${t(quality)}`;
  $("qualityBadge").className = `pill ${["ok", "complete"].includes(quality) ? "ok" : quality === "partial" ? "partial" : "error"}`;
  $("resultSummary").textContent = `${result.model} · ${t("detectHint")}`;
  $("metricGrid").innerHTML = [metric(t("observations"), stats.observation_count || 0), metric(t("candidates"), stats.candidate_count || 0), metric(t("legendEntries"), result.legend.entry_count || 0), metric(t("tokens"), formatTokens(result.tokens || 0))].join("");
  if (result.estimated_cost_usd != null) $("metricGrid").innerHTML += metric(t("estimatedCost"), `$${Number(result.estimated_cost_usd).toFixed(4)}`);
  $("runPath").textContent = job.run_dir || "";
  if (result.pause_reason) $("resultSummary").textContent = `${result.pause_reason} · ${state.language === "zh-CN" ? "已保存检查点；选择续跑可继续未完成部分。" : "Checkpoints saved. Choose Resume to continue incomplete coverage."}`;
}

async function openResults({jobId = null, runDir = null, uploadId = null, errorId = "resultError"} = {}) {
  const errorNode = $(errorId); errorNode.classList.add("hidden");
  try {
    if (!runDir) runDir = state.job?.run_dir;
    if (uploadId) {
      await api("/api/detection-source", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({run_dir:runDir, upload_id:uploadId})});
    }
    location.href = `/detections?${new URLSearchParams({run_dir:runDir})}`;
  } catch (error) { errorNode.textContent = error.message; errorNode.classList.remove("hidden"); }
}

async function loadRecentRuns() {
  try {
    const payload = await api("/api/runs");
    window.__recentRuns = payload.runs || [];
    renderRecentRuns(window.__recentRuns);
  } catch (_error) { /* dashboard remains usable */ }
}

function renderRecentRuns(runs) {
  $("recentSection").classList.toggle("hidden", !runs.length);
  $("recentRuns").innerHTML = "";
  const query = ($("runFilter")?.value || "").trim().toLowerCase();
  const visibleRuns = query
    ? runs.filter((run) => [run.diagram, run.filename, run.run_id, run.model, run.engine, run.quality_status].some((value) => String(value || "").toLowerCase().includes(query)))
    : runs;
  for (const run of visibleRuns) {
    const row = document.createElement("div");
    row.className = "recent-run";
    const details = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = `${run.diagram || run.filename} · ${run.run_id || ""}`;
    const meta = document.createElement("div");
    meta.className = "recent-run-meta";
    for (const value of [
      run.finished_at,
      run.engine,
      run.model,
      run.quality_status,
      run.has_detection ? `${run.observation_count || 0} ${t("observations")}` : t("unsupported"),
    ]) {
      const item = document.createElement("span");
      item.textContent = value || "";
      meta.append(item);
    }
    details.append(title, meta);
    const actions = document.createElement("div");
    actions.className = "recent-run-actions";
    const sourceState = document.createElement("span");
    sourceState.className = `source-state ${run.source_available ? "available" : "missing"}`;
    sourceState.textContent = run.source_available
      ? t(run.source_verified ? "sourceVerified" : "sourceFound")
      : t("sourceNeeded");
    const button = document.createElement("button");
    button.className = "primary";
    button.disabled = !run.has_detection;
    button.textContent = run.source_verified ? t("viewResults") : t("attachSource");
    button.addEventListener("click", () => {
      if (run.source_verified) openResults({runDir:run.run_dir, errorId:"existingResultError"});
      else { state.pendingSourceRun = run; $("existingSourceInput").click(); }
    });
    actions.append(sourceState, button);
    if (run.has_detection && !run.source_verified) {
      const results = document.createElement("button"); results.className = "quiet"; results.textContent = t("viewResults");
      results.onclick = () => openResults({runDir:run.run_dir, errorId:"existingResultError"}); actions.append(results);
    }
    row.append(details, actions);
    $("recentRuns").append(row);
  }
}

async function restoreActiveJob() {
  try {
    const payload = await api("/api/jobs");
    const job = payload.jobs?.[0];
    if (!job) return;
    state.job = job;
    state.logCursor = 0;
    state.logLines = [];
    $("runSection").classList.remove("hidden");
    renderJob(job);
    startElapsedClock();
    await pollJob();
  } catch (_error) { /* no in-memory jobs after a server restart */ }
}

async function initialise() {
  $("languageSwitch").value = state.language;
  applyLanguage();
  try {
    state.config = await api("/api/config");
    $("modelPolicy").value = state.config.model_policy || "evaluation";
    state.connected = true;
    $("serverStatus").classList.add("online");
    $("serverStatus").querySelector("span").textContent = t("online");
    $("provider").value = state.config.provider;
    $("baseUrl").value = state.config.base_url || providerDefaults[state.config.provider] || "";
    $("visionModel").value = state.config.vision_model || state.config.model || "";
    $("reasoningModel").value = state.config.reasoning_model || state.config.model || "";
    $("reasoningMode").value = state.config.reasoning_mode || "auto";
    $("providerOrder").value = (state.config.openrouter_provider_order || []).join(", ");
    $("providerIgnore").value = (state.config.openrouter_provider_ignore || []).join(", ");
    $("providerFallbacks").value = String(state.config.openrouter_allow_fallbacks !== false);
    $("effort").value = state.config.effort || "medium";
    updateProvider();
    updateModelPolicy();
    await Promise.all([loadRecentRuns(), restoreActiveJob()]);
  } catch (error) {
    $("serverStatus").querySelector("span").textContent = error.message;
  }
}

$("languageSwitch").addEventListener("change", () => { state.language = $("languageSwitch").value; localStorage.setItem("diagex.web.language", state.language); applyLanguage(); });
$("provider").addEventListener("change", () => { useCustomModels(); updateProvider(); });
function updateModelConstraintHint() {
  const models = [$("visionModel").value, $("reasoningModel").value];
  const hints = [];
  if (models.some(model => /(?:^|\/)glm-5\.3(?:$|[-:])/i.test(model))) hints.push(t("glmReasoning"));
  if (models.includes("qwen/qwen3-vl-235b-a22b-instruct")) hints.push(t("qwenReasoning"));
  $("modelConstraintHint").textContent = $("provider").value === "openrouter" ? hints.join(" ") : "";
}
function useCustomModels() { $("modelPolicy").value = "evaluation"; updateModelConstraintHint(); }
function updateModelPolicy() {
  const profile = state.config?.model_profiles?.[$("modelPolicy").value];
  if (profile) {
    $("provider").value = profile.provider;
    $("visionModel").value = profile.vision_model;
    $("reasoningModel").value = profile.escalation_model === profile.vision_model ? "" : profile.escalation_model;
    $("baseUrl").value = providerDefaults[profile.provider];
    updateProvider();
  }
  updateModelConstraintHint();
}
$("modelPolicy").addEventListener("change", updateModelPolicy);
for (const id of ["visionModel", "reasoningModel"]) $(id).addEventListener("input", useCustomModels);
$("refreshModels").addEventListener("click", loadOpenRouterModels);
$("toggleKey").addEventListener("click", () => { const visible = $("apiKey").type === "text"; $("apiKey").type = visible ? "password" : "text"; $("toggleKey").textContent = t(visible ? "show" : "hide"); });
$("fileInput").addEventListener("change", () => { if ($("fileInput").files[0]) uploadFile($("fileInput").files[0]).catch((error) => { $("formError").textContent = error.message; $("formError").classList.remove("hidden"); $("dropZone").classList.remove("hidden"); }); });
$("replaceFile").addEventListener("click", () => { state.upload = null; $("fileSummary").classList.add("hidden"); $("dropZone").classList.remove("hidden"); $("fileInput").value = ""; $("startButton").disabled = true; });
for (const event of ["dragenter", "dragover"]) $("dropZone").addEventListener(event, (e) => { e.preventDefault(); $("dropZone").classList.add("dragging"); });
for (const event of ["dragleave", "drop"]) $("dropZone").addEventListener(event, (e) => { e.preventDefault(); $("dropZone").classList.remove("dragging"); });
$("dropZone").addEventListener("drop", (event) => { const file = event.dataTransfer.files[0]; if (file) uploadFile(file).catch((error) => { $("formError").textContent = error.message; $("formError").classList.remove("hidden"); $("dropZone").classList.remove("hidden"); }); });
$("startButton").addEventListener("click", () => startExtraction());
$("viewResultsButton").addEventListener("click", () => openResults({jobId:state.job?.id}));
$("copyLog").addEventListener("click", async () => { await navigator.clipboard.writeText(state.logLines.join("\n")); showToast(t("copied")); });
$("refreshRuns").addEventListener("click", loadRecentRuns);
$("runFilter").addEventListener("input", () => renderRecentRuns(window.__recentRuns || []));
$("existingSourceInput").addEventListener("change", async () => {
  const file = $("existingSourceInput").files[0];
  const run = state.pendingSourceRun;
  $("existingSourceInput").value = "";
  if (!file || !run) return;
  $("existingResultError").classList.add("hidden");
  showToast(t("sourceUploading"));
  try {
    const payload = await uploadDrawing(file);
    await openResults({
      runDir: run.run_dir,
      uploadId: payload.upload.id,
      errorId: "existingResultError",
    });
    await loadRecentRuns();
  } catch (error) {
    $("existingResultError").textContent = error.message;
    $("existingResultError").classList.remove("hidden");
  } finally {
    state.pendingSourceRun = null;
  }
});

initialise();
