"""Hệ thống giao diện: chủ đề màu, chủ đề theo dịp lễ, chế độ sáng/tối, nền động nhẹ không cản trở đọc."""
from __future__ import annotations

import datetime as dt
from urllib.parse import quote

# primary: màu chủ đạo · accent: màu nhấn · land: 3 tông cho dãy núi/rừng ở nền · particle: hạt rơi (None = không có)
THEMES = {
    "Rừng xanh": {"primary": "#0F766E", "accent": "#14B8A6", "land": ("#99F6E4", "#5EEAD4", "#0F766E"), "particle": None, "icon": "🌲"},
    "Thiên nhiên": {"primary": "#3F6212", "accent": "#84CC16", "land": ("#D9F99D", "#A3E635", "#4D7C0F"), "particle": None, "icon": "🌿"},
    "Đại dương": {"primary": "#1D4ED8", "accent": "#0EA5E9", "land": ("#BAE6FD", "#7DD3FC", "#1D4ED8"), "particle": None, "icon": "🌊"},
    "Hoàng hôn": {"primary": "#C2410C", "accent": "#F59E0B", "land": ("#FED7AA", "#FDBA74", "#C2410C"), "particle": None, "icon": "🌅"},
    "Ngày Nhà giáo": {"primary": "#BE185D", "accent": "#F472B6", "land": ("#FBCFE8", "#F9A8D4", "#BE185D"), "particle": "#F9A8D4", "icon": "💐"},
    "Giáng sinh": {"primary": "#B91C1C", "accent": "#15803D", "land": ("#DCFCE7", "#86EFAC", "#166534"), "particle": "#FFFFFF", "icon": "🎄"},
    "Tết Nguyên đán": {"primary": "#B91C1C", "accent": "#EAB308", "land": ("#FEF08A", "#FDE047", "#B91C1C"), "particle": "#FACC15", "icon": "🧧"},
    "Trung thu": {"primary": "#7C3AED", "accent": "#F59E0B", "land": ("#EDE9FE", "#C4B5FD", "#5B21B6"), "particle": "#FCD34D", "icon": "🏮"},
}
AUTO = "Tự động theo dịp"
CUSTOM = "Tùy chỉnh"


def seasonal(today: dt.date | None = None) -> str:
    """Chọn chủ đề theo dịp (mốc gần đúng theo dương lịch)."""
    d = today or dt.date.today()
    md = (d.month, d.day)
    if (11, 15) <= md <= (11, 25):
        return "Ngày Nhà giáo"
    if (12, 10) <= md <= (12, 31):
        return "Giáng sinh"
    if (1, 15) <= md <= (2, 25):
        return "Tết Nguyên đán"
    if (9, 1) <= md <= (9, 30):
        return "Trung thu"
    return "Rừng xanh"


def resolve(name: str, custom: dict | None = None) -> tuple[str, dict]:
    if name == AUTO:
        name = seasonal()
    if name == CUSTOM and custom:
        p, a = custom.get("primary", "#0F766E"), custom.get("accent", "#14B8A6")
        return CUSTOM, {"primary": p, "accent": a, "land": (_mix(a, "#FFFFFF", .7), _mix(a, "#FFFFFF", .45), p), "particle": None, "icon": "🎨"}
    return name, THEMES.get(name, THEMES["Rừng xanh"])


def _mix(c1: str, c2: str, t: float) -> str:
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x * (1 - t) + y * t):02X}" for x, y in zip(a, b))


def _landscape_svg(land: tuple, dark: bool) -> str:
    """Dãy núi + rừng thông phẳng (flat illustration), dùng làm lớp nền cuối trang."""
    c1, c2, c3 = land
    if dark:
        c1, c2, c3 = _mix(c1, "#0B1220", .75), _mix(c2, "#0B1220", .7), _mix(c3, "#0B1220", .55)
    trees = "".join(
        f'<polygon points="{x},{y - h} {x - w},{y} {x + w},{y}" fill="{c3}"/><polygon points="{x},{y - h * 1.5:.0f} {x - w * .75:.0f},{y - h * .55:.0f} {x + w * .75:.0f},{y - h * .55:.0f}" fill="{c3}"/>'
        for x, y, w, h in [(90, 300, 26, 46), (150, 310, 20, 36), (1250, 296, 30, 52), (1325, 308, 22, 40), (1395, 300, 26, 46), (520, 318, 16, 30), (985, 316, 18, 32)])
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 400" preserveAspectRatio="xMidYMax slice">'
           f'<path d="M0 230 L160 120 L300 210 L470 90 L640 220 L820 110 L1000 230 L1180 100 L1440 220 V400 H0Z" fill="{c1}"/>'
           f'<path d="M0 290 L200 190 L380 280 L560 180 L760 290 L960 200 L1160 290 L1440 200 V400 H0Z" fill="{c2}"/>'
           f'{trees}'
           f'<path d="M0 330 C 300 300, 520 360, 760 330 S 1200 300, 1440 335 V400 H0Z" fill="{c3}"/></svg>')
    return "data:image/svg+xml;utf8," + quote(svg)


def css(name: str, dark: bool, motion: bool, custom: dict | None = None) -> str:
    label, t = resolve(name, custom)
    p, a = t["primary"], t["accent"]
    if dark:
        v = dict(bg="#0B1220", card="#111A2E", card2="#17223A", text="#E5E9F0", muted="#94A3B8", border="#24324D",
                 side1=_mix(p, "#0B1220", .82), side2="#0F172A", sidetext="#E5E9F0", sidehover=_mix(p, "#0B1220", .65))
    else:
        v = dict(bg=_mix(a, "#FFFFFF", .94), card="#FFFFFF", card2="#F6F8FA", text="#1F2D3D", muted="#64748B", border="#E3E7EC",
                 side1="#FFFFFF", side2=_mix(a, "#FFFFFF", .86), sidetext="#1F2D3D", sidehover=_mix(a, "#FFFFFF", .78))
    land = _landscape_svg(t["land"], dark)
    blob_a = 0.16 if not dark else 0.22
    particle = t["particle"]
    anim = "" if motion else "animation:none !important;"
    parts = ""
    if particle and motion:
        dots = ",".join(f"radial-gradient(circle {r}px at {x}% {y}%, {particle} 98%, transparent 100%)"
                        for x, y, r in [(5, 10, 3), (18, 40, 2), (30, 5, 3), (44, 60, 2), (58, 20, 3), (70, 75, 2), (82, 35, 3), (93, 55, 2), (12, 80, 2), (64, 90, 3)])
        parts = f"""
  .bg-particles {{position:fixed; inset:-100% 0 0 0; height:200%; pointer-events:none; z-index:-1; opacity:{.45 if not dark else .35};
    background-image:{dots}; background-size:100% 50%; animation:fall 60s linear infinite;}}
  @keyframes fall {{from {{transform:translateY(0)}} to {{transform:translateY(50%)}}}}"""
    return f"""
<style>
  :root {{--primary:{p}; --accent:{a}; --bg:{v['bg']}; --card:{v['card']}; --card2:{v['card2']}; --text:{v['text']}; --muted:{v['muted']};
         --border:{v['border']}; --side1:{v['side1']}; --side2:{v['side2']}; --sidetext:{v['sidetext']}; --sidehover:{v['sidehover']};}}
  .stApp {{background:var(--bg) !important; color:var(--text);}}
  /* ---- nền động: 2 đốm màu trôi rất chậm + dãy núi/rừng mờ ở chân trang ---- */
  .bg-blobs {{position:fixed; inset:0; pointer-events:none; z-index:-1;
    background:radial-gradient(40vw 40vw at 15% 20%, {p}{int(blob_a * 255):02X}, transparent 70%),
               radial-gradient(45vw 45vw at 85% 70%, {a}{int(blob_a * 255):02X}, transparent 70%);
    background-size:140% 140%; animation:drift 45s ease-in-out infinite alternate; {anim}}}
  @keyframes drift {{0% {{background-position:0% 0%, 100% 100%}} 100% {{background-position:30% 20%, 70% 80%}}}}
  .bg-land {{position:fixed; left:0; right:0; bottom:0; height:30vh; pointer-events:none; z-index:-1; opacity:{.32 if not dark else .5};
    background:url("{land}") bottom center / cover no-repeat; animation:sway 80s ease-in-out infinite alternate; {anim}}}
  @keyframes sway {{from {{transform:translateX(0)}} to {{transform:translateX(-2%)}}}}{parts}
  @media (prefers-reduced-motion: reduce) {{ .bg-blobs, .bg-land, .bg-particles {{animation:none !important;}} }}
  [data-testid="stMain"] {{position:relative; z-index:0; background:transparent !important;}}
  [data-testid="stHeader"] {{background:transparent;}}
  /* ---- chữ & thẻ ---- */
  .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp p, .stApp li, .stApp label, .stApp span, .stMarkdown, .cardh {{color:var(--text);}}
  .cardsub, .crumb, .stApp [data-testid="stCaptionContainer"] * {{color:var(--muted) !important;}}
  .crumb b {{color:var(--primary) !important;}}
  [class*="st-key-card_"] {{background:var(--card) !important; border:1px solid var(--border) !important; border-radius:12px !important;
    box-shadow:0 2px 10px rgba(0,0,0,{.05 if not dark else .35});}}
  .kpi {{background:var(--card); border-color:var(--border);}} .kpi .v {{color:var(--text);}}
  .flowx div {{background:var(--card2); border-color:var(--border); color:var(--text);}} .flowx div span {{color:var(--primary);}}
  .sug {{background:var(--card); border-color:var(--border); border-left-color:var(--primary);}} .sug b {{color:var(--text);}}
  .hero {{background:linear-gradient(120deg, {p} 0%, {_mix(p, a, .45)} 65%, {a} 140%) !important;}}
  .stButton button[kind="primary"], .stDownloadButton button[kind="primary"], [data-testid="stFormSubmitButton"] button {{background:var(--primary) !important; border-color:var(--primary) !important;}}
  .stButton button[kind="primary"] *, [data-testid="stFormSubmitButton"] button * {{color:#FFFFFF !important;}}
  .stTabs [aria-selected="true"] {{color:var(--primary) !important;}} .stTabs [data-baseweb="tab-highlight"] {{background:var(--primary) !important;}}
  /* ---- ô nhập trong chế độ tối ---- */
  {'''.stApp input, .stApp textarea, .stApp [data-baseweb="select"] > div, .stApp [data-baseweb="input"], .stApp [data-baseweb="textarea"] {background:var(--card2) !important; color:var(--text) !important; border-color:var(--border) !important;}
  .stApp [data-testid="stExpander"] details, .stApp [data-testid="stFileUploaderDropzone"], .stApp [data-testid="stPopover"] button, .stApp .stButton button[kind="secondary"] {background:var(--card2) !important; color:var(--text) !important; border-color:var(--border) !important;}
  .cp {background:#3A2E12 !important;} .ok {background:#12301D !important;} .al.do {background:#3B1518;} .al.vang {background:#3A2E12;} .al.xanh {background:#12301D;}''' if dark else ''}
  /* ---- thanh bên sáng sủa ---- */
  [data-testid="stSidebar"] {{background:linear-gradient(180deg, var(--side1) 0%, var(--side2) 100%) !important; border-right:1px solid var(--border);}}
  [data-testid="stSidebar"] * {{color:var(--sidetext) !important;}}
  [data-testid="stSidebar"] .brand, [data-testid="stSidebar"] .user {{border-bottom-color:var(--border) !important;}}
  [data-testid="stSidebar"] .brand .lg {{background:var(--primary) !important; color:#fff !important;}}
  [data-testid="stSidebar"] .user .av {{background:var(--accent) !important; color:#fff !important;}}
  [data-testid="stSidebar"] .sec {{color:var(--muted) !important;}}
  [data-testid="stSidebar"] .brand b {{color:var(--sidetext) !important;}}
  [data-testid="stSidebar"] .stButton button:disabled {{opacity:.5;}}
  [data-testid="stSidebar"] .stButton button {{background:transparent !important; border:none !important;}}
  [data-testid="stSidebar"] .stButton button:hover {{background:var(--sidehover) !important;}}
  [data-testid="stSidebar"] .stButton button[kind="primary"] {{background:var(--primary) !important; box-shadow:0 2px 8px {p}55;}}
  [data-testid="stSidebar"] .stButton button[kind="primary"] * {{color:#FFFFFF !important;}}
  [data-testid="stSidebar"] input, [data-testid="stSidebar"] [data-baseweb="select"] > div {{background:var(--card) !important; color:var(--text) !important; border:1px solid var(--border) !important;}}
  [data-testid="stSidebar"] [data-testid="stExpander"] {{background:var(--card) !important; border-color:var(--border) !important;}}
</style>
<div class="bg-blobs"></div><div class="bg-land"></div>{'<div class="bg-particles"></div>' if parts else ''}
"""
