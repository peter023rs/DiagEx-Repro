"""Static, local reviewer for deterministically reconstructed legend tables."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from diagex.extractors.evidence_checkpoint import atomic_write_json, atomic_write_text
from diagex.vision.legend_tables import AbbreviationInventory
from diagex.vision.loader import iter_pages
from diagex.vision.models import DiagramSource


def write_abbreviation_review(
    *, run_dir: Path, source: DiagramSource, inventory: AbbreviationInventory, source_hash: str
) -> tuple[Path, Path]:
    """Write row crops, machine-readable coverage, and a self-contained reviewer."""
    crop_dir = run_dir / "legend-row-images"
    rows = [row.model_dump(mode="json") for row in inventory.rows]
    rows_by_page: dict[int, list[tuple[int, dict[str, Any]]]] = {}
    for index, row in enumerate(rows):
        rows_by_page.setdefault(int(row["page_index"]), []).append((index, row))

    for page in iter_pages(source):
        targets = rows_by_page.get(page.page_index, [])
        if not targets or page.image is None:
            continue
        crop_dir.mkdir(exist_ok=True)
        for index, row in targets:
            box = row["row_bbox"]
            padding = max(10, int(box["h"] * 0.35))
            x0, y0 = max(0, box["x"] - padding), max(0, box["y"] - padding)
            x1 = min(page.width, box["x"] + box["w"] + padding)
            y1 = min(page.height, box["y"] + box["h"] + padding)
            crop = page.image.crop((x0, y0, x1, y1))
            name = f"row-{index + 1:04d}-{row['id']}.png"
            crop.save(crop_dir / name, format="PNG")
            row["source_crop"] = f"legend-row-images/{name}"

    payload = {
        "schema_version": "1.0.0",
        "source_sha256": source_hash,
        "summary": inventory.summary,
        "sections": inventory.sections,
        "rows": rows,
        "review_note": (
            "Rows are reconstructed from positioned native PDF text. Review decisions in "
            "legend.review.html are stored in this browser until a reviewed JSON file is downloaded."
        ),
    }
    json_path = run_dir / "legend.abbreviations.json"
    html_path = run_dir / "legend.review.html"
    atomic_write_json(json_path, payload)
    atomic_write_text(html_path, _review_html(payload))
    return json_path, html_path


def _review_html(payload: dict[str, Any]) -> str:
    data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    title = html.escape("DiagEx legend table review / 图例表复核")
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
:root{{--blue:#2563eb;--green:#15803d;--red:#b91c1c;--amber:#b45309;--line:#d8dee9;--muted:#64748b}}
*{{box-sizing:border-box}} body{{margin:0;font:14px/1.45 system-ui,-apple-system,sans-serif;color:#172033;background:#f5f7fa}}
header{{position:sticky;top:0;z-index:3;background:white;border-bottom:1px solid var(--line);padding:12px 18px}}
h1{{font-size:20px;margin:0 0 9px}} .bar{{display:flex;gap:8px;align-items:center;flex-wrap:wrap}}
button,select,input{{font:inherit;border:1px solid #bdc7d6;border-radius:6px;background:white;padding:7px 9px}}
button.primary{{background:var(--blue);color:white;border-color:var(--blue)}} .summary{{color:var(--muted);margin-left:auto}}
main{{max-width:1500px;margin:auto;padding:16px}} .section{{background:white;border:1px solid var(--line);border-radius:10px;margin-bottom:14px;overflow:hidden}}
.section h2{{font-size:16px;margin:0;padding:12px 14px;border-bottom:1px solid var(--line)}}
.row{{display:grid;grid-template-columns:230px 105px minmax(210px,1fr) 180px 150px 145px;gap:10px;align-items:center;padding:10px 14px;border-bottom:1px solid #edf0f4}}
.row:last-child{{border-bottom:0}} .row.issue{{background:#fff8ed}} .crop{{height:72px;width:220px;object-fit:contain;object-position:left center;background:white;border:1px solid #e2e8f0}}
.code{{font-weight:700;font-size:16px}} .meaning input,.normal input,.normal select{{width:100%;margin-top:3px}} .printed{{font-weight:600;margin:3px 0 5px}} .meta{{font-size:12px;color:var(--muted)}}
.status.approved{{color:var(--green)}} .status.rejected{{color:var(--red)}} .pill{{display:inline-block;padding:2px 6px;border-radius:999px;background:#eef2ff;font-size:12px}}
.warning{{color:var(--amber);font-size:12px}} .empty{{padding:30px;text-align:center;color:var(--muted)}}
@media(max-width:1050px){{.row{{grid-template-columns:190px 90px minmax(180px,1fr) 150px}}.review,.normal{{grid-column:auto/span 2}}.crop{{width:180px}}}}
</style></head><body>
<header><h1>DiagEx 图例表复核 <span style="color:#64748b;font-weight:400">Legend table review</span></h1>
<div class="bar">
<select id="section"><option value="all">全部表 / All tables</option><option value="general">通用缩写</option><option value="instrument_type">仪表类型缩写</option></select>
<select id="filter"><option value="all">全部状态 / All</option><option value="unreviewed">待复核 / Unreviewed</option><option value="issues">仅问题 / Issues</option><option value="approved">已批准 / Approved</option><option value="rejected">已拒绝 / Rejected</option></select>
<input id="search" placeholder="搜索代码或含义 / Search" size="26">
<button id="approveVisible">批准当前可见项 / Approve visible</button>
<button class="primary" id="download">下载复核 JSON / Download reviewed JSON</button>
<span class="summary" id="summary"></span></div></header>
<main id="app"></main>
<script>const DATA={data};
const key='diagex-legend-review-'+DATA.source_sha256; let saved={{}}; try{{saved=JSON.parse(localStorage.getItem(key)||'{{}}')}}catch(e){{}}
const esc=s=>String(s??'').replace(/[&<>\"]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]));
function state(row){{const old=saved[row.id]||{{}};return {{status:'unreviewed',canonical_code:row.canonical_code,description:old.description??old.raw_description??row.raw_description,kind:row.kind,symbol_class:row.symbol_class,...old}}}}
function persist(){{localStorage.setItem(key,JSON.stringify(saved));renderSummary()}}
function setValue(id,k,v){{const row=DATA.rows.find(r=>r.id===id);saved[id]={{...state(row),[k]:v}};persist()}}
function issue(row){{return row.warnings.length||Object.values(DATA.summary.conflicts||{{}}).some(v=>v.includes(row.raw_description)&&DATA.rows.filter(r=>r.canonical_code===row.canonical_code).length>1)}}
function visible(row){{const s=state(row),q=document.querySelector('#search').value.trim().toLowerCase(),sec=document.querySelector('#section').value,f=document.querySelector('#filter').value;if(sec!=='all'&&row.section!==sec)return false;if(q&&!`${{row.canonical_code}} ${{row.raw_description}}`.toLowerCase().includes(q))return false;if(f==='issues'&&!issue(row))return false;if(!['all','issues'].includes(f)&&s.status!==f)return false;return true}}
function render(){{const groups={{general:[],instrument_type:[]}};DATA.rows.filter(visible).forEach(r=>groups[r.section].push(r));let out='';for(const [section,rows] of Object.entries(groups)){{if(!rows.length)continue;const heading=section==='general'?'通用缩写 / General abbreviations':'仪表类型缩写 / Instrument-type abbreviations';out+=`<div class="section"><h2>${{heading}} · ${{rows.length}}</h2>`;for(const row of rows){{const s=state(row),conf=(DATA.summary.conflicts||{{}})[row.canonical_code];const kinds=['equipment','instrument','line','valve','connector','other'];out+=`<div class="row ${{issue(row)?'issue':''}}"><div>${{row.source_crop?`<img class="crop" src="${{esc(row.source_crop)}}">`:'<div class="crop empty">无图 / no crop</div>'}}<div class="meta">第 ${{row.page_index+1}} 页 · (${{row.row_bbox.x}}, ${{row.row_bbox.y}})</div></div><div><div class="code">${{esc(row.printed_code)}}</div><span class="pill">${{esc(row.section)}}</span></div><div class="meaning"><label>图纸原文 / Printed source</label><div class="printed">${{esc(row.raw_description)}}</div><label>复核含义 / Reviewed meaning</label><input value="${{esc(s.description)}}" onchange="setValue('${{row.id}}','description',this.value)">${{conf?`<div class="warning">同代码多种定义: ${{esc(conf.join(' / '))}}</div>`:''}}</div><div class="normal"><label>规范代码 / Normalized</label><input value="${{esc(s.canonical_code)}}" onchange="setValue('${{row.id}}','canonical_code',this.value)"><select onchange="setValue('${{row.id}}','kind',this.value)">${{kinds.map(k=>`<option ${{s.kind===k?'selected':''}}>${{k}}</option>`).join('')}}</select><input aria-label="symbol class" value="${{esc(s.symbol_class)}}" onchange="setValue('${{row.id}}','symbol_class',this.value)"></div><div class="review"><select class="status ${{s.status}}" onchange="setValue('${{row.id}}','status',this.value);render()"><option value="unreviewed" ${{s.status==='unreviewed'?'selected':''}}>待复核 / Unreviewed</option><option value="approved" ${{s.status==='approved'?'selected':''}}>批准 / Approve</option><option value="rejected" ${{s.status==='rejected'?'selected':''}}>拒绝 / Reject</option></select></div><div class="meta">来源 IDs: ${{row.source_ids.length}}<br>置信度: ${{row.confidence}}</div></div>`}}out+='</div>'}}document.querySelector('#app').innerHTML=out||'<div class="empty">没有符合筛选条件的项目 / No matching rows</div>';renderSummary()}}
function renderSummary(){{let a=0,r=0;DATA.rows.forEach(row=>{{const s=state(row).status;a+=s==='approved';r+=s==='rejected'}});document.querySelector('#summary').textContent=`${{DATA.rows.length}} 行 · 已批准 ${{a}} · 已拒绝 ${{r}} · 待复核 ${{DATA.rows.length-a-r}}`}}
['section','filter','search'].forEach(id=>document.querySelector('#'+id).addEventListener(id==='search'?'input':'change',render));
document.querySelector('#approveVisible').onclick=()=>{{DATA.rows.filter(visible).forEach(row=>saved[row.id]={{...state(row),status:'approved'}});persist();render()}};
document.querySelector('#download').onclick=()=>{{const reviewed={{...DATA,reviewed_at:new Date().toISOString(),review:DATA.rows.map(row=>({{id:row.id,...state(row)}}))}};const b=new Blob([JSON.stringify(reviewed,null,2)],{{type:'application/json'}}),a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='legend.abbreviations.reviewed.json';a.click();URL.revokeObjectURL(a.href)}};render();
</script></body></html>"""
