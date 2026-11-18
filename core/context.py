"""BƯỚC 1 — Tiếp nhận & thấu hiểu bối cảnh doanh nghiệp."""
from __future__ import annotations

import io

from .llm import LLMClient

NA = "Chưa cung cấp"


def extract_text(name: str, data: bytes, max_chars: int = 30000) -> str:
    """Trích văn bản từ PDF / DOCX / PPTX / TXT / MD."""
    ext = name.lower().rsplit(".", 1)[-1]
    text = ""
    try:
        if ext == "pdf":
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(data))
            text = "\n".join((p.extract_text() or "") for p in reader.pages)
        elif ext == "docx":
            import docx

            d = docx.Document(io.BytesIO(data))
            parts = [p.text for p in d.paragraphs if p.text.strip()]
            for t in d.tables:  # từ điển dữ liệu thường nằm trong bảng
                for row in t.rows:
                    parts.append(" | ".join(c.text.strip() for c in row.cells))
            text = "\n".join(parts)
        elif ext == "pptx":
            from pptx import Presentation

            prs = Presentation(io.BytesIO(data))
            parts = []
            for i, slide in enumerate(prs.slides, 1):
                parts.append(f"--- Slide {i} ---")
                for shp in slide.shapes:
                    if shp.has_text_frame:
                        parts.append(shp.text_frame.text)
                    if getattr(shp, "has_table", False) and shp.has_table:
                        for row in shp.table.rows:
                            parts.append(" | ".join(c.text for c in row.cells))
            text = "\n".join(parts)
        else:
            text = data.decode("utf-8", errors="ignore")
    except Exception as exc:
        text = f"[Lỗi đọc tệp {name}: {exc}]"
    return text[:max_chars]


import re

FIELD_PATTERNS = {  # nhãn người dùng hay viết -> trường hồ sơ
    "name": r"t[eê]n (c[oô]ng ty|doanh nghi[eệ]p)|c[oô]ng ty|doanh nghi[eệ]p",
    "industry": r"l[iĩ]nh v[uự]c|ng[aà]nh",
    "business_model": r"m[oô] h[iì]nh|k[eê]nh b[aá]n|kh[aá]ch h[aà]ng m[uụ]c ti[eê]u",
    "scale": r"quy m[oô]|nh[aâ]n s[uự]|chi nh[aá]nh|c[uử]a h[aà]ng",
    "goal": r"m[uụ]c ti[eê]u|v[aấ]n [dđ][eề]|th[aá]ch th[uứ]c|b[aà]i to[aá]n|c[aầ]n tr[aả] l[oờ]i",
    "kpi": r"kpi|ch[iỉ] s[oố]",
    "time": r"th[oờ]i gian|giai [dđ]o[aạ]n|k[yỳ] ph[aâ]n t[ií]ch",
    "region": r"th[iị] tr[uư][oờ]ng|khu v[uự]c|ph[aạ]m vi",
    "data": r"d[uữ] li[eệ]u|t[uừ] [dđ]i[eể]n|c[oộ]t",
}
KPI_TERMS = ["doanh thu", "lợi nhuận ròng", "lợi nhuận", "CAC", "ROAS", "ROI", "tỷ lệ chuyển đổi", "giá trị đơn hàng", "AOV",
             "thị phần", "chi phí", "churn", "tỷ lệ rời bỏ", "LTV", "biên lợi nhuận", "số đơn"]


def _clean(v: str) -> str:
    return re.sub(r"\s+", " ", v).strip(" .;:-–")


def _heuristic(text: str) -> dict:
    """Trích xuất có chọn lọc khi không có mô hình ngôn ngữ: đọc các dòng 'Nhãn: nội dung' và từ khoá."""
    found: dict[str, list[str]] = {}
    lines = [l.strip(" •-*\t") for l in re.split(r"[\r\n]+", text) if l.strip()]
    free = []
    for i, line in enumerate(lines):
        m = re.match(r"^([^:]{2,45}):\s*(.+)$", line)
        if m:
            label, val = m.group(1).lower(), _clean(m.group(2))
            for k, pat in FIELD_PATTERNS.items():
                if re.search(pat, label):
                    found.setdefault(k, []).append(val)
                    break
            else:
                free.append(line)
        elif i == 0 and len(line) <= 60 and not line.endswith("."):
            found.setdefault("name", []).append(_clean(line))  # dòng đầu ngắn thường là tên doanh nghiệp
        else:
            free.append(line)
    whole = " ".join(lines)
    if "time" not in found:
        t = re.findall(r"(?:t[uừ]\s*)?\d{1,2}/\d{4}\s*(?:[-–đến]+\s*\d{1,2}/\d{4})?|qu[yý]\s*[1-4]/?\d{0,4}|n[aă]m\s*20\d{2}", whole, re.I)
        if t:
            found["time"] = [_clean(x) for x in t[:2]]
    if "region" not in found:
        r = re.findall(r"(qu[oố]c t[eế]|to[aà]n qu[oố]c|H[aà] N[oộ]i|TP\.?\s?HCM|[DĐ][aà] N[aẵ]ng|[DĐ]ông Nam [AÁ]|Vi[eệ]t Nam)", whole, re.I)
        if r:
            found["region"] = list(dict.fromkeys(r))
    kpis = [k for k in KPI_TERMS if re.search(rf"(?<!\w){re.escape(k)}(?!\w)", whole, re.I)]
    kpis = [k for k in kpis if not any(k != o and k.lower() in o.lower() for o in kpis)]  # bỏ từ bị bao bởi từ dài hơn
    if "business_model" not in found:
        bm = re.findall(r"\b(B2B|B2C|B2B2C|SaaS|th[uư][oơ]ng m[aạ]i [dđ]i[eệ]n t[uử]|b[aá]n l[eẻ]|ph[aâ]n ph[oố]i)\b", whole, re.I)
        if bm:
            found["business_model"] = list(dict.fromkeys(x for x in bm))
    j = lambda k: "; ".join(found.get(k, []))  # noqa: E731
    goal = j("goal") or (free[0] if free else "")
    # Tách mục tiêu thành các trọng tâm phân tích
    if re.search(r"gi[aả]m|s[uụ]t|nguy[eê]n nh[aâ]n|t[uụ]t", goal, re.I):
        first = _clean(re.split(r"\.\s", goal)[0])
        questions = [f"Nguyên nhân nào khiến {first[0].lower() + first[1:]}?", "Nhóm nào (kênh, khu vực, sản phẩm) kéo lùi kết quả nhiều nhất?",
                     "Cần ưu tiên hành động nào để phục hồi chỉ số?"]
    else:
        parts = [_clean(x) for x in re.split(r",|;| và | thông qua ", goal) if len(_clean(x)) > 8 and not _clean(x).lower().startswith("việc")][:4]
        questions = [f"Làm thế nào để {p[0].lower() + p[1:]}?" for p in parts]
    name = j("name")
    summary_bits = []
    if name or j("industry"):
        summary_bits.append(f"{name or 'Doanh nghiệp'}{' hoạt động trong lĩnh vực ' + j('industry')[0].lower() + j('industry')[1:] if j('industry') else ''}")
    if j("scale"):
        summary_bits.append(j("scale")[0].lower() + j("scale")[1:])
    summary = ", ".join(summary_bits) + "." if summary_bits else ""
    if goal:
        summary += f" Trọng tâm cần giải quyết: {goal[0].lower() + goal[1:]}."
    return {
        "summary": summary.strip(),
        "company_overview": {"name": name, "industry": j("industry"), "business_model": j("business_model"), "scale_operations": j("scale")},
        "objectives": {"main_problem": goal, "key_questions": questions},
        "data_constraints": {"assumptions": found.get("data", []), "data_dictionary": [], "time_scope": j("time"), "region_scope": j("region")},
        "kpi_hint": ", ".join(kpis) if kpis else j("kpi"),
        "missing_info": [],
    }


def _missing(p: dict) -> list[str]:
    co, ob, dc = p["company_overview"], p["objectives"], p["data_constraints"]
    need = [("lĩnh vực hoạt động", co.get("industry")), ("mô hình kinh doanh", co.get("business_model")), ("vấn đề cần giải quyết", ob.get("main_problem")),
            ("chỉ số cần theo dõi", p.get("kpi_hint")), ("giai đoạn phân tích", dc.get("time_scope")), ("thị trường / khu vực", dc.get("region_scope"))]
    return [n for n, v in need if not _filled(v)]


def _filled(v) -> bool:
    return bool(v) and str(v).strip().lower() not in ("chưa cung cấp", "không rõ", "n/a", "none", "")


def build_profile(llm: LLMClient, user_text: str, docs_text: str, previous: dict | None = None, feedback: str | None = None) -> dict:
    source = user_text + ("\n" + docs_text if docs_text else "") + ("\n" + feedback if feedback else "")
    heur = _heuristic(source)
    prompt = (
        "NHIỆM VỤ (Bước 1): Đọc thông tin doanh nghiệp người dùng cung cấp, CHẮT LỌC và TÓM TẮT lại thành hồ sơ bối cảnh.\n"
        "QUY TẮC:\n- summary: 2–3 câu viết lại bằng lời của bạn, nêu doanh nghiệp là ai, đang gặp vấn đề gì, cần phân tích để làm gì.\n"
        "- Mỗi trường chỉ điền khi thông tin có trong nguồn hoặc suy ra trực tiếp (ví dụ 'SaaS & thiết bị công nghệ' → mô hình B2B và B2C). Viết ngắn gọn, KHÔNG chép nguyên câu dài.\n"
        "- Trường không có thông tin: để chuỗi rỗng \"\" (không viết 'Chưa cung cấp').\n"
        "- key_questions: 2–4 câu hỏi phân tích cụ thể suy ra từ mục tiêu.\n- kpi_hint: các chỉ số người dùng quan tâm (ví dụ CAC, lợi nhuận ròng).\n\n"
        f"NGUỒN — MÔ TẢ CỦA NGƯỜI DÙNG:\n{user_text or '(trống)'}\n\nNGUỒN — TÀI LIỆU ĐÍNH KÈM:\n{docs_text or '(không có)'}\n\n"
    )
    if previous and feedback:
        prompt += f"HỒ SƠ TRƯỚC:\n{previous}\n\nYÊU CẦU CHỈNH SỬA (ưu tiên cao nhất):\n{feedback}\n\n"
    prompt += ('Trả về JSON: {"summary": "", "company_overview": {"name": "", "industry": "", "business_model": "", "scale_operations": ""}, '
               '"objectives": {"main_problem": "", "key_questions": [""]}, "data_constraints": {"assumptions": [""], '
               '"data_dictionary": [{"column": "", "meaning": ""}], "time_scope": "", "region_scope": ""}, "kpi_hint": ""}')
    prof = llm.json(prompt, fallback=heur) or heur
    for k, v in heur.items():  # trường LLM bỏ trống thì lấy từ trích xuất theo quy tắc
        if isinstance(v, dict):
            prof.setdefault(k, {})
            for kk, vv in v.items():
                if not _filled(prof[k].get(kk)) and vv:
                    prof[k][kk] = vv
        elif not _filled(prof.get(k)) and v:
            prof[k] = v
    prof["missing_info"] = _missing(prof)
    return prof


def profile_markdown(p: dict) -> str:
    """Hiển thị đúng những gì người dùng cung cấp; không in các ô trống."""
    co, ob, dc = p["company_overview"], p["objectives"], p["data_constraints"]
    L = []
    if p.get("summary"):
        L += ["#### 📝 Tóm tắt bối cảnh", p["summary"]]
    biz = [(lbl, co.get(k)) for lbl, k in (("Doanh nghiệp", "name"), ("Lĩnh vực", "industry"), ("Mô hình kinh doanh", "business_model"), ("Quy mô", "scale_operations"))]
    biz = [(a, b) for a, b in biz if _filled(b)]
    if biz:
        L.append("#### 🏢 Doanh nghiệp")
        L += [f"- **{a}:** {b}" for a, b in biz]
    if _filled(ob.get("main_problem")) or ob.get("key_questions") or _filled(p.get("kpi_hint")):
        L.append("#### 🎯 Mục tiêu phân tích")
        if _filled(ob.get("main_problem")):
            L.append(f"- **Vấn đề cần giải quyết:** {ob['main_problem']}")
        if _filled(p.get("kpi_hint")):
            L.append(f"- **Chỉ số quan tâm:** {p['kpi_hint']}")
        qs = [q for q in ob.get("key_questions") or [] if _filled(q)]
        if qs:
            L.append("- **Câu hỏi phân tích:**")
            L += [f"  - {q}" for q in qs]
    sc = [(a, b) for a, b in (("Giai đoạn", dc.get("time_scope")), ("Thị trường / khu vực", dc.get("region_scope"))) if _filled(b)]
    sc += [("Ghi chú dữ liệu", a) for a in dc.get("assumptions") or [] if _filled(a)]
    dd = [d for d in (dc.get("data_dictionary") or []) if isinstance(d, dict) and _filled(d.get("column"))]
    if sc or dd:
        L.append("#### 📊 Phạm vi và dữ liệu")
        L += [f"- **{a}:** {b}" for a, b in sc]
        L += [f"- `{d['column']}`: {d.get('meaning', '')}" for d in dd]
    if p.get("missing_info"):
        L.append(f"\n> ℹ️ Có thể bổ sung để phân tích sát hơn: {', '.join(p['missing_info'])}.")
    return "\n".join(L)
