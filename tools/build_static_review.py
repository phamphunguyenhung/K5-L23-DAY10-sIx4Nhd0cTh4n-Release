"""Build a zero-backend static visual review site with separated Detection and Segment views."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


MEMBERS = [
    "@hungpixi",
    "@AnhHoangDepTrai",
    "@buivanthinhtxt-del",
    "@ngxuanviet",
    "@trahoangdev",
    "@Soraxolo",
]

PALETTE = [
    (220, 38, 38),
    (37, 99, 235),
    (22, 163, 74),
    (217, 119, 6),
    (147, 51, 234),
    (8, 145, 178),
    (219, 39, 119),
    (101, 163, 13),
]


def load_classes(delivery: Path) -> list[str]:
    return [line.strip() for line in (delivery / "classes.txt").read_text(encoding="utf-8").splitlines() if line.strip()]


def load_panoptic_map(delivery: Path) -> tuple[dict[int, str], dict[str, list[dict]]]:
    data = json.loads((delivery / "panoptic.json").read_text(encoding="utf-8"))
    cats = {c["id"]: c["name"] for c in data.get("categories", [])}
    anns = {}
    for ann in data.get("annotations", []):
        stem = Path(ann["file_name"]).stem
        anns[stem] = ann.get("segments_info", [])
    return cats, anns


def render_three_panels(
    delivery: Path,
    image_id: str,
    classes: list[str],
    cats: dict[int, str],
    pan_anns: dict[str, list[dict]],
    out_assets: Path,
) -> dict[str, str]:
    img_dir = out_assets / image_id
    img_dir.mkdir(parents=True, exist_ok=True)
    orig_out = img_dir / "orig.jpg"
    det_out = img_dir / "det.png"
    seg_out = img_dir / "seg.png"

    src_img = delivery / "images" / f"{image_id}.jpg"
    if not src_img.exists():
        # Fallback placeholder if missing_image rule error
        im = Image.new("RGB", (640, 480), (241, 245, 249))
        d = ImageDraw.Draw(im)
        d.text((20, 20), f"Missing image: {image_id}", fill=(220, 38, 38))
        im.save(orig_out)
        im.save(det_out)
        im.save(seg_out)
        return {
            "orig": f"assets/{image_id}/orig.jpg",
            "det": f"assets/{image_id}/det.png",
            "seg": f"assets/{image_id}/seg.png",
        }

    base = Image.open(src_img).convert("RGB")
    w, h = base.size
    if not orig_out.exists():
        base.save(orig_out, quality=88)

    font = ImageFont.load_default()

    # 1) Detection ONLY
    if not det_out.exists():
        det_im = base.copy()
        draw = ImageDraw.Draw(det_im)
        lbl_path = delivery / "labels" / f"{image_id}.txt"
        if lbl_path.exists():
            for idx, line in enumerate(lbl_path.read_text(encoding="utf-8").splitlines()):
                parts = line.strip().split()
                if len(parts) < 5:
                    continue
                cls_id = int(float(parts[0]))
                cx, cy, bw, bh = map(float, parts[1:5])
                x1 = max(0, int((cx - bw / 2) * w))
                y1 = max(0, int((cy - bh / 2) * h))
                x2 = min(w - 1, int((cx + bw / 2) * w))
                y2 = min(h - 1, int((cy + bh / 2) * h))
                color = PALETTE[idx % len(PALETTE)]
                draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
                cname = classes[cls_id] if 0 <= cls_id < len(classes) else f"cls_{cls_id}"
                label = f"{cname}"
                tb = draw.textbbox((x1, max(0, y1 - 14)), label, font=font)
                draw.rectangle([tb[0] - 2, tb[1] - 1, tb[2] + 2, tb[3] + 1], fill=color)
                draw.text((x1, max(0, y1 - 14)), label, fill=(255, 255, 255), font=font)
        det_im.save(det_out)

    # 2) Segment ONLY
    if not seg_out.exists():
        seg_im = base.convert("RGBA")
        mask_path = delivery / "masks" / f"{image_id}.png"
        if mask_path.exists():
            mask_rgb = Image.open(mask_path).convert("RGB")
            if mask_rgb.size != (w, h):
                mask_rgb = mask_rgb.resize((w, h), Image.NEAREST)
            # Decode RGB -> segment_id
            import numpy as np  # optional fast path; fallback pure PIL if missing
        seg_out_img = base.convert("RGBA")
        if mask_path.exists():
            px = mask_rgb.getdata()
            overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            ov_px = overlay.load()
            segs = pan_anns.get(image_id, [])
            seg_meta = {s["id"]: s for s in segs}
            seg_colors = {s["id"]: PALETTE[i % len(PALETTE)] for i, s in enumerate(segs)}
            # Fast bounding/centroid tracking for labels
            boxes: dict[int, list[int]] = {}
            for y in range(h):
                row_off = y * w
                for x in range(w):
                    r, g, b = px[row_off + x]
                    sid = r + (g << 8) + (b << 16)
                    if sid in seg_colors:
                        c = seg_colors[sid]
                        ov_px[x, y] = (c[0], c[1], c[2], 95)
                        if sid not in boxes:
                            boxes[sid] = [x, y, x, y]
                        else:
                            bx = boxes[sid]
                            if x < bx[0]: bx[0] = x
                            if y < bx[1]: bx[1] = y
                            if x > bx[2]: bx[2] = x
                            if y > bx[3]: bx[3] = y
            seg_out_img = Image.alpha_composite(seg_out_img, overlay).convert("RGB")
            sdraw = ImageDraw.Draw(seg_out_img)
            for sid, bx in boxes.items():
                info = seg_meta.get(sid, {})
                cat_name = cats.get(info.get("category_id", -1), str(info.get("category_id", "?")))
                c = seg_colors[sid]
                sdraw.rectangle(bx, outline=c, width=2)
                tx, ty = bx[0] + 2, max(0, bx[1] + 2)
                tb = sdraw.textbbox((tx, ty), cat_name, font=font)
                sdraw.rectangle([tb[0] - 2, tb[1] - 1, tb[2] + 2, tb[3] + 1], fill=c)
                sdraw.text((tx, ty), cat_name, fill=(255, 255, 255), font=font)
        else:
            seg_out_img = seg_out_img.convert("RGB")
        seg_out_img.save(seg_out)

    return {
        "orig": f"assets/{image_id}/orig.jpg",
        "det": f"assets/{image_id}/det.png",
        "seg": f"assets/{image_id}/seg.png",
    }


def build_html(items: list[dict]) -> str:
    data_json = json.dumps(items, ensure_ascii=False)
    members_json = json.dumps(MEMBERS, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Day10 Visual Review — Tách Detection &amp; Segment</title>
  <style>
    :root {{ --bg: #f8fafc; --card: #ffffff; --text: #0f172a; --muted: #475569; --border: #cbd5e1; --primary: #2563eb; --ok: #16a34a; --bad: #dc2626; --warn: #d97706; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; background: var(--bg); color: var(--text); font-size: 15px; }}
    header {{ position: sticky; top: 0; z-index: 20; background: #fff; border-bottom: 1px solid var(--border); padding: 14px 24px; display: flex; flex-wrap: wrap; gap: 12px; align-items: center; justify-content: space-between; }}
    h1 {{ margin: 0; font-size: 20px; font-weight: 800; }}
    .tabs {{ display: flex; flex-wrap: wrap; gap: 8px; padding: 14px 24px 0; }}
    .tab {{ height: 38px; padding: 0 14px; border: 1px solid var(--border); background: #fff; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 14px; color: var(--text); }}
    .tab.active {{ background: var(--primary); color: #fff; border-color: var(--primary); }}
    .actions {{ display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }}
    .btn {{ height: 38px; padding: 0 14px; border-radius: 8px; border: 1px solid var(--border); background: #fff; cursor: pointer; font-weight: 600; font-size: 14px; }}
    .btn-primary {{ background: var(--primary); color: #fff; border-color: var(--primary); }}
    .main {{ width: 100%; padding: 16px 24px 48px; display: grid; gap: 18px; }}
    .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 16px; }}
    .card-head {{ display: flex; flex-wrap: wrap; gap: 10px; align-items: center; justify-content: space-between; margin-bottom: 12px; }}
    .badges {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }}
    .badge {{ padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 700; background: #e2e8f0; color: #0f172a; }}
    .badge.EASY {{ background: #dcfce7; color: #166534; }}
    .badge.MEDIUM {{ background: #fef3c7; color: #92400e; }}
    .badge.HARD {{ background: #fee2e2; color: #991b1b; }}
    .evidence {{ font-family: ui-monospace, monospace; font-size: 13px; background: #f1f5f9; padding: 6px 10px; border-radius: 6px; margin-bottom: 12px; }}
    .panels {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin-bottom: 12px; }}
    @media (max-width: 960px) {{ .panels {{ grid-template-columns: 1fr; }} }}
    .panel {{ border: 1px solid var(--border); border-radius: 8px; overflow: hidden; background: #fff; }}
    .panel-title {{ padding: 6px 10px; font-size: 13px; font-weight: 700; background: #f1f5f9; border-bottom: 1px solid var(--border); }}
    .panel img {{ width: 100%; height: auto; display: block; cursor: zoom-in; }}
    .controls {{ display: grid; grid-template-columns: auto auto 1fr; gap: 10px; align-items: center; }}
    @media (max-width: 900px) {{ .controls {{ grid-template-columns: 1fr; }} }}
    .verdict-group {{ display: flex; gap: 6px; }}
    .vbtn {{ height: 38px; padding: 0 12px; border-radius: 8px; border: 1px solid var(--border); background: #fff; cursor: pointer; font-weight: 700; font-size: 13px; }}
    .vbtn.confirmed.active {{ background: var(--ok); color: #fff; border-color: var(--ok); }}
    .vbtn.rejected.active {{ background: var(--bad); color: #fff; border-color: var(--bad); }}
    .vbtn.skipped.active {{ background: var(--warn); color: #fff; border-color: var(--warn); }}
    select, input[type=text] {{ height: 38px; padding: 0 10px; border: 1px solid var(--border); border-radius: 8px; font-size: 14px; background: #fff; color: var(--text); }}
    .note-wrap {{ display: flex; gap: 8px; align-items: center; }}
    .note-wrap input {{ flex: 1; min-width: 220px; }}
    .char-count {{ font-size: 12px; font-weight: 700; min-width: 68px; text-align: right; }}
    .char-ok {{ color: var(--ok); }}
    .char-low {{ color: var(--bad); }}
    .modal {{ display: none; position: fixed; inset: 0; background: rgba(15,23,42,.85); z-index: 50; align-items: center; justify-content: center; padding: 20px; }}
    .modal.open {{ display: flex; }}
    .modal img {{ max-width: 95vw; max-height: 92vh; border-radius: 8px; background: #fff; }}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>Day10 Visual Review (de_an_01) — Tách Detection &amp; Segment</h1>
      <div id="stats" style="font-size:13px;color:var(--muted);margin-top:4px;"></div>
    </div>
    <div class="actions">
      <button class="btn btn-primary" onclick="exportCsv(true)">Export CSV (Người đang chọn)</button>
      <button class="btn" onclick="exportCsv(false)">Export CSV (Tất cả)</button>
    </div>
  </header>
  <div class="tabs" id="tabs"></div>
  <main class="main" id="list"></main>
  <div class="modal" id="modal" onclick="this.classList.remove('open')"><img id="modalImg" src="" alt="zoom" /></div>
  <script>
    const ITEMS = {data_json};
    const MEMBERS = {members_json};
    const STORAGE_KEY = 'day10_de_an_01_reviews_v1';
    let state = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{{}}');
    let currentMember = MEMBERS[0];

    function saveState() {{
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
      renderTabs();
      updateStats();
    }}

    function updateStats() {{
      const visible = currentMember === 'ALL' ? ITEMS : ITEMS.filter(x => x.reviewer === currentMember);
      const done = visible.filter(x => {{
        const s = state[x.key];
        return s && (s.verdict === 'confirmed' || s.verdict === 'rejected') && (s.note || '').trim().length >= 20;
      }}).length;
      document.getElementById('stats').textContent = `Đang xem: ${{currentMember}} · Hợp lệ (verdict + note >=20 ký tự): ${{done}} / ${{visible.length}}`;
    }}

    function renderTabs() {{
      const el = document.getElementById('tabs');
      el.innerHTML = '';
      const all = [...MEMBERS, 'ALL'];
      all.forEach(m => {{
        const items = m === 'ALL' ? ITEMS : ITEMS.filter(x => x.reviewer === m);
        const done = items.filter(x => state[x.key]?.verdict).length;
        const b = document.createElement('button');
        b.className = 'tab' + (currentMember === m ? ' active' : '');
        b.textContent = (m === 'ALL' ? 'Tất cả' : m) + ` (${{done}}/${{items.length}})`;
        b.onclick = () => {{ currentMember = m; renderTabs(); renderList(); updateStats(); }};
        el.appendChild(b);
      }});
    }}

    function setVerdict(key, verdict) {{
      state[key] = state[key] || {{ type: ITEMS.find(x => x.key === key).type, note: '' }};
      state[key].verdict = verdict;
      saveState();
      renderList();
    }}

    function setType(key, type) {{
      state[key] = state[key] || {{ note: '' }};
      state[key].type = type;
      saveState();
    }}

    function setNote(key, note, countEl) {{
      state[key] = state[key] || {{ type: ITEMS.find(x => x.key === key).type }};
      state[key].note = note;
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
      const len = note.trim().length;
      countEl.textContent = `${{len}}/20`;
      countEl.className = 'char-count ' + (len >= 20 ? 'char-ok' : 'char-low');
      updateStats();
    }}

    function zoom(src) {{
      document.getElementById('modalImg').src = src;
      document.getElementById('modal').classList.add('open');
    }}

    function csvEscape(v) {{
      const s = String(v ?? '');
      return /[",\\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
    }}

    function exportCsv(onlyCurrent) {{
      const subset = (onlyCurrent && currentMember !== 'ALL') ? ITEMS.filter(x => x.reviewer === currentMember) : ITEMS;
      const lines = ['image,type,verdict,note'];
      subset.forEach(it => {{
        const s = state[it.key];
        if (!s || !s.verdict || s.verdict === 'skipped') return;
        lines.push([it.image_id, s.type || it.type, s.verdict, (s.note || '').trim()].map(csvEscape).join(','));
      }});
      const blob = new Blob([lines.join('\\n') + '\\n'], {{ type: 'text/csv;charset=utf-8;' }});
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      const tag = (onlyCurrent && currentMember !== 'ALL') ? currentMember.replace('@', '') : 'all';
      a.download = `review_log_${{tag}}.csv`;
      a.click();
    }}

    function renderList() {{
      const el = document.getElementById('list');
      el.innerHTML = '';
      const visible = currentMember === 'ALL' ? ITEMS : ITEMS.filter(x => x.reviewer === currentMember);
      visible.forEach((it, idx) => {{
        const s = state[it.key] || {{ type: it.type, verdict: '', note: '' }};
        const len = (s.note || '').trim().length;
        const card = document.createElement('section');
        card.className = 'card';
        card.innerHTML = `
          <div class="card-head">
            <div class="badges">
              <span class="badge">#${{idx + 1}} · ${{it.image_id}}</span>
              <span class="badge">${{it.type}}</span>
              <span class="badge ${{it.tier}}">${{it.tier}}</span>
              <span class="badge">score: ${{it.score}}</span>
              <span class="badge">Reviewer: ${{it.reviewer}}</span>
            </div>
          </div>
          <div class="evidence">Evidence: ${{it.evidence}}</div>
          <div class="panels">
            <div class="panel">
              <div class="panel-title">1. Ảnh gốc (Original)</div>
              <img src="${{it.orig}}" loading="lazy" onclick="zoom('${{it.orig}}')" />
            </div>
            <div class="panel">
              <div class="panel-title">2. Detection (YOLO Boxes)</div>
              <img src="${{it.det}}" loading="lazy" onclick="zoom('${{it.det}}')" />
            </div>
            <div class="panel">
              <div class="panel-title">3. Segment (Panoptic Mask)</div>
              <img src="${{it.seg}}" loading="lazy" onclick="zoom('${{it.seg}}')" />
            </div>
          </div>
          <div class="controls">
            <div class="verdict-group">
              <button class="vbtn confirmed ${{s.verdict==='confirmed'?'active':''}}" onclick="setVerdict('${{it.key}}','confirmed')">CONFIRM</button>
              <button class="vbtn rejected ${{s.verdict==='rejected'?'active':''}}" onclick="setVerdict('${{it.key}}','rejected')">REJECT</button>
              <button class="vbtn skipped ${{s.verdict==='skipped'?'active':''}}" onclick="setVerdict('${{it.key}}','skipped')">SKIP</button>
            </div>
            <select onchange="setType('${{it.key}}', this.value)">
              ${{['class_swap','category_swap','bbox_drift','missing_box','instance_merge'].map(t => `<option value="${{t}}" ${{(s.type||it.type)===t?'selected':''}}>${{t}}</option>`).join('')}}
            </select>
            <div class="note-wrap">
              <input type="text" placeholder="Ghi rõ thấy gì trong ảnh (>= 20 ký tự)..." value="${{(s.note||'').replace(/"/g, '&quot;')}}" oninput="setNote('${{it.key}}', this.value, this.nextElementSibling)" />
              <span class="char-count ${{len>=20?'char-ok':'char-low'}}">${{len}}/20</span>
            </div>
          </div>
        `;
        el.appendChild(card);
      }});
    }}

    renderTabs();
    renderList();
    updateStats();
  </script>
</body>
</html>"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--delivery", required=True)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    delivery = Path(args.delivery)
    run_dir = Path(args.run_dir)
    out_dir = Path(args.out_dir)
    assets_dir = out_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    classes = load_classes(delivery)
    cats, pan_anns = load_panoptic_map(delivery)
    cands = json.loads((run_dir / "candidates.json").read_text(encoding="utf-8")).get("candidates", [])

    # Read triage assignments, fixing any 'Họ và tên' header artifact
    triage_map: dict[tuple[str, str], dict] = {}
    with (run_dir / "triage.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("kind") != "rule":
                triage_map[(r["image_id"], r["candidate_type"])] = r

    items = []
    overflow_idx = 0
    for idx, c in enumerate(cands):
        img_id = c["target"]
        ctype = c["type"]
        tr = triage_map.get((img_id, ctype), {})
        rev = tr.get("assigned_reviewer", "")
        if rev not in MEMBERS:
            rev = MEMBERS[overflow_idx % len(MEMBERS)]
            overflow_idx += 1
        paths = render_three_panels(delivery, img_id, classes, cats, pan_anns, assets_dir)
        items.append({
            "key": f"{idx}_{img_id}_{ctype}",
            "image_id": img_id,
            "type": ctype,
            "tier": tr.get("difficulty_tier", "MEDIUM"),
            "score": c.get("score", 0),
            "evidence": c.get("evidence", ""),
            "reviewer": rev,
            **paths,
        })

    (out_dir / "index.html").write_text(build_html(items), encoding="utf-8")
    print(f"Built static review site: {out_dir / 'index.html'} ({len(items)} items)")


if __name__ == "__main__":
    main()
