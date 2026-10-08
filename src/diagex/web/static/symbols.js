const $ = (id) => document.getElementById(id);
const words = {
  en: {back:"Back to detection", eyebrow:"DRAWING REFERENCES", title:"Symbol library", intro:"Original legend crops, names, and traceable sources for symbol detection.", priority:"Your drawing's legend comes first", trust:"Machine extractions and starter definitions are reference material, pending verification. References from other drawings are not applied automatically.", coverage:"Standards and coverage", search:"Search names, classes, or sources", source:"Source", allSources:"All sources", project:"Project legends", type:"Show", images:"Symbols with images", all:"All definitions", abbreviations:"Abbreviations", uncertain:"Uncertain / rejected", more:"Show more", choose:"Select a symbol to inspect its source and definition.", noImage:"Text only - no source image", catalogImage:"Official index only - image unavailable", machine_extracted:"Machine extracted", unverified_starter:"Unverified starter", customer_override:"Customer override", catalog_only:"Catalog metadata only", reject:"Rejected", uncertainStatus:"Uncertain", classification:"Class", page:"Source page", bounds:"Crop bounds (source pixels)", origin:"Original source", provenance:"Import history", id:"Database ID", noResults:"No matching definitions. Change your search or filters.", sourceLink:"Publisher source", loadError:"Could not load the symbol library. Reload to retry.", empty:"No symbol database is installed. Import the project legends first.", detection:"Detection use", reference:"Reference hint only. The current drawing's legend and visible source ink take priority.", excluded:"Excluded from detection references.", scoped:"Used only for the same source drawing; fresh runs skip stored project references."},
  "zh-CN": {back:"返回检测", eyebrow:"图纸参考", title:"符号库", intro:"原始图例裁剪、名称和可追溯来源，为符号检测提供参考。", priority:"当前图纸的图例优先", trust:"机器提取和初始定义均为待核验的参考资料。其他图纸的图例不会自动应用。", coverage:"标准与收录范围", search:"搜索名称、类别或来源", source:"来源", allSources:"全部来源", project:"项目图例", type:"显示", images:"含图像的符号", all:"全部定义", abbreviations:"缩写", uncertain:"不确定 / 已拒绝", more:"显示更多", choose:"选择符号，查看来源和定义。", noImage:"仅文字，暂无原始图像", catalogImage:"仅官方索引，图像未获取", machine_extracted:"机器提取", unverified_starter:"未核验初始定义", customer_override:"用户覆盖定义", catalog_only:"仅目录信息", reject:"已拒绝", uncertainStatus:"不确定", classification:"类别", page:"来源页码", bounds:"裁剪坐标（原图像素）", origin:"原始来源", provenance:"导入记录", id:"数据库 ID", noResults:"没有匹配的定义，请调整搜索或筛选条件。", sourceLink:"出版方来源", loadError:"符号库加载失败，请刷新重试。", empty:"尚未安装符号数据库，请先导入项目图例。", detection:"检测用途", reference:"仅作参考，当前图纸的图例和可见图形优先。", excluded:"不用于检测参考。", scoped:"仅用于相同来源图纸；全新运行不使用已存储的项目图例。"}
};
Object.assign(words.en, {document_reference:"Document reference", category:"Printed category", document:"Source document", pdfBounds:"Image bounds (PDF points)", truncated:"Name is truncated in the source PDF; retained as printed.", exclusion:"Exclusion reason"});
Object.assign(words["zh-CN"], {document_reference:"文献参考", category:"原文分类", document:"来源文档", pdfBounds:"图像坐标（PDF 点）", truncated:"原 PDF 中名称已被截断，此处按原文保留。", exclusion:"排除原因"});
let language = localStorage.getItem("diagex.web.language") || "en";
if (!words[language]) language = "en";
let data = {symbols:[], standards:[], summary:{}}, selected = null, limit = 48;
const t = (key) => words[language][key] || key;
const status = (row) => t(row.status === "uncertain" ? "uncertainStatus" : row.status);
function el(tag, text, className) {
  const node = document.createElement(tag);
  if (text != null) node.textContent = text;
  if (className) node.className = className;
  return node;
}
function link(url, text) {
  const a = el("a", text);
  if (url && /^https:\/\//.test(url)) { a.href = url; a.target = "_blank"; a.rel = "noopener noreferrer"; }
  return a;
}
function preview(row) {
  const box = el("div", null, "symbol-preview");
  if (row.image_path) {
    const image = el("img"); image.src = `/api/symbol-image?id=${encodeURIComponent(row.id)}`;
    image.alt = row.name; image.loading = "lazy"; box.append(image);
  } else box.append(el("span", t(row.status === "catalog_only" ? "catalogImage" : "noImage")));
  return box;
}
function inspect(row, scroll = false) {
  selected = row;
  const box = $("detail"); box.replaceChildren(preview(row), el("h2", row.name), el("span", status(row), "pill"), el("p", row.description));
  const dl = el("dl");
  const field = (label, text) => { if (text != null && text !== "") dl.append(el("dt", t(label)), el("dd", text)); };
  field("classification", [row.kind, row.symbol_class].filter(Boolean).join(" / "));
  field("page", row.page); field(row.attributes.source_bbox_units?.startsWith("PDF") ? "pdfBounds" : "bounds", row.bbox ? `x ${row.bbox.x}, y ${row.bbox.y}, w ${row.bbox.w}, h ${row.bbox.h}` : null);
  field("category", row.attributes.source_category);
  field("document", row.attributes.source_document);
  field("exclusion", row.attributes.reference_exclusion);
  if (row.attributes.source_name_truncated === "true") box.append(el("p", t("truncated")));
  const sources = [...new Map(row.sources.map(s => [s.path, s])).values()];
  field("origin", (sources.find(s => s.source_ref.startsWith("built-in:")) || sources[0])?.source_ref);
  const standard = data.standards.find(s => s.id === row.standard);
  if (standard?.url) { dl.append(el("dt", t("sourceLink"))); const dd = el("dd"); dd.append(link(standard.url, standard.title)); dl.append(dd); }
  else if (row.attributes.source_url) { dl.append(el("dt", t("sourceLink"))); const dd = el("dd"); dd.append(link(row.attributes.source_url, row.attributes.source_publisher || row.attributes.source_url)); dl.append(dd); }
  field("detection", ["catalog_only", "reject", "uncertain"].includes(row.status) ? t("excluded") : row.scope.startsWith("legend:") ? t("scoped") : t("reference"));
  box.append(dl);
  const history = el("details"); history.append(el("summary", `${t("provenance")} (${sources.length})`));
  for (const source of sources) {
    const p = el("p");
    if (/^https:\/\//.test(source.path)) p.append(link(source.path, source.path)); else p.append(el("code", source.path));
    if (source.document_sha256) p.append(el("br"), el("code", `SHA-256: ${source.document_sha256}`));
    history.append(p);
  }
  box.append(history, el("p", t("id")), el("code", row.id));
  for (const card of document.querySelectorAll(".symbol-card")) card.setAttribute("aria-pressed", String(card.dataset.id === row.id));
  if (scroll && window.innerWidth <= 900) box.scrollIntoView({behavior:"instant", block:"start"});
}
function render() {
  const q = $("search").value.trim().toLocaleLowerCase(), source = $("source").value, type = $("type").value;
  const rows = data.symbols.filter(row => {
    if (source === "project" && !row.scope.startsWith("legend:")) return false;
    if (source && source !== "project" && row.standard !== source && row.attributes.reference_collection !== source) return false;
    if (type === "images" && !row.image_path) return false;
    if (type === "abbreviation" && row.attributes.legend_kind !== "abbreviation") return false;
    if (type === "uncertain" && !["uncertain", "reject"].includes(row.status)) return false;
    return !q || [row.name, row.description, row.symbol_class, row.standard, row.attributes.source_category, ...row.sources.map(s => `${s.path} ${s.source_ref}`)].join(" ").toLocaleLowerCase().includes(q);
  });
  $("count").textContent = language === "zh-CN" ? `${rows.length} 条匹配定义 · 共 ${data.symbols.length} 条记录（保留历史版本）` : `${rows.length} matching definitions · ${data.symbols.length} records, including historical variants`;
  $("grid").replaceChildren();
  for (const row of rows.slice(0, limit)) {
    const card = el("button", null, "symbol-card"); card.type = "button"; card.dataset.id = row.id;
    card.setAttribute("aria-pressed", String(selected?.id === row.id));
    const caption = el("div", null, "symbol-caption");
    caption.append(el("strong", row.name), el("small", row.attributes.source_publisher || row.standard || t("project")), el("span", status(row), "pill"));
    card.append(preview(row), caption); card.addEventListener("click", () => inspect(row, true)); $("grid").append(card);
  }
  if (!rows.length) $("grid").append(el("p", t(data.symbols.length ? "noResults" : "empty")));
  $("more").hidden = rows.length <= limit;
}
function translate() {
  document.documentElement.lang = language;
  document.title = `${t("title")} | DiagEx`;
  $("language").value = language;
  for (const node of document.querySelectorAll("[data-t]")) node.textContent = t(node.dataset.t);
  $("standards").replaceChildren();
  for (const standard of data.standards) {
    const block = el("div"); block.append(standard.url ? link(standard.url, standard.title) : el("strong", standard.title), el("p", standard.coverage));
    $("standards").append(block);
  }
  render(); if (selected) inspect(selected);
}
$("language").addEventListener("change", () => { language = $("language").value; localStorage.setItem("diagex.web.language", language); translate(); });
for (const id of ["search", "source", "type"]) $(id).addEventListener(id === "search" ? "input" : "change", () => {
  if (id === "source" && $("source").value && $("source").value !== "project" && $("type").value === "images") $("type").value = "all";
  limit = 48; render();
});
$("more").addEventListener("click", () => { limit += 48; render(); });
const initialSource = new URLSearchParams(window.location.search).get("source");
if ([...$("source").options].some(option => option.value === initialSource)) $("source").value = initialSource;
translate();
fetch("/api/symbols").then(response => { if (!response.ok) throw new Error(response.status); return response.json(); }).then(value => { data = value; translate(); }).catch(() => { $("count").textContent = t("loadError"); });
