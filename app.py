"""
Phân tích Dữ liệu Kinh doanh — giao diện Streamlit kiểu bảng quản trị.
Chạy:  streamlit run app.py
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd
import streamlit as st

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass
try:  # Streamlit Cloud: khóa đặt trong Secrets
    for _k in ("GEMINI_API_KEY", "GEMINI_MODEL"):
        if _k in st.secrets and not os.getenv(_k):
            os.environ[_k] = str(st.secrets[_k])
except Exception:
    pass

from core import auth
from core import dashboard as D
from core import pipeline as P
from core import suggest as SG
from core import theme as TH
from core.context import extract_text
from core.dashboard import interactive
from core.llm import LLMClient
from core.narrative import HORIZONS

st.set_page_config(page_title="Phân tích Dữ liệu Kinh doanh", page_icon="📊", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
  .stApp {background:#F4F6F9;}
  [data-testid="stHeader"] {background:transparent; height:2.6rem;}
  .block-container {padding-top:3.2rem; padding-bottom:3rem; max-width:1500px;}
  h1, h2, h3, h4 {color:#1F2D3D;}
  /* ---------- thanh bên tối kiểu bảng quản trị ---------- */
  [data-testid="stSidebar"] .brand {display:flex; align-items:center; gap:10px; padding:4px 4px 14px 4px; border-bottom:1px solid #4B545C; margin-bottom:12px;}
  [data-testid="stSidebar"] .brand .lg {width:34px; height:34px; border-radius:50%; background:#E07A1F; display:flex; align-items:center; justify-content:center; color:#fff !important; font-weight:800;}
  [data-testid="stSidebar"] .brand b {color:#fff !important; font-size:1.05rem;}
  [data-testid="stSidebar"] .user {display:flex; align-items:center; gap:10px; padding:4px 4px 12px 4px; border-bottom:1px solid #4B545C; margin-bottom:10px;}
  [data-testid="stSidebar"] .user .av {width:32px; height:32px; border-radius:50%; background:#6C757D; display:flex; align-items:center; justify-content:center; color:#fff !important; font-weight:700;}
  [data-testid="stSidebar"] .sec {font-size:.72rem; letter-spacing:1px; text-transform:uppercase; color:#8A939B !important; margin:10px 0 4px 6px;}
  [data-testid="stSidebar"] .stButton button > div, [data-testid="stSidebar"] .stButton button p {justify-content:flex-start !important; text-align:left !important; width:100%;}
  [data-testid="stSidebar"] .stButton button {justify-content:flex-start; border:none; background:transparent; padding:.42rem .75rem; border-radius:6px; font-weight:500;}
  [data-testid="stSidebar"] .stButton button:hover {background:#494E53;}
  [data-testid="stSidebar"] .stButton button[kind="primary"] {background:#1F6FEB; }
  [data-testid="stSidebar"] .stButton button[kind="primary"] * {color:#fff !important;}
  [data-testid="stSidebar"] .stButton button:disabled {opacity:.38;}
  [data-testid="stSidebar"] input {background:#454D55 !important; color:#fff !important;}
  [data-testid="stSidebar"] [data-testid="stExpander"] {border-color:#4B545C; background:#3B4148;}
  /* ---------- thẻ nội dung ---------- */
  [data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"]) {background:#FFFFFF; border-radius:10px; border:1px solid #E3E7EC !important; box-shadow:0 1px 3px rgba(0,0,0,.06);}
  .topbar {display:flex; justify-content:space-between; align-items:flex-end; margin:0 0 14px 0;}
  .topbar h2 {margin:0; padding:0; font-size:1.7rem; font-weight:700;}
  .crumb {font-size:.85rem; color:#6C757D;} .crumb b {color:#1F6FEB; font-weight:600;}
  .cardh {font-weight:700; font-size:1.02rem; color:#1F2D3D; margin-bottom:2px;}
  .cardsub {font-size:.85rem; color:#6C757D; margin-bottom:6px;}
  .cp {border-left:5px solid #F0A500; background:#FFF8E6; border-radius:8px; padding:12px 16px; margin:8px 0;}
  .ok {border-left:5px solid #28A745; background:#ECF8EF; border-radius:8px; padding:10px 16px; margin:8px 0;}
  .kpi {border-radius:10px; padding:16px 18px; background:#FFFFFF; border:1px solid #E3E7EC; box-shadow:0 1px 3px rgba(0,0,0,.05);}
  .kpi .lb {font-size:.78rem; color:#6C757D; font-weight:600; text-transform:uppercase; letter-spacing:.4px;}
  .kpi .v {font-size:1.6rem; font-weight:800; color:#1F2D3D; margin:4px 0;}
  .kpi .d {font-size:.86rem; font-weight:700;}
  .up {color:#28A745;} .down {color:#DC3545;} .flat {color:#6C757D;}
  .al {border-radius:8px; padding:9px 13px; margin:6px 0; font-weight:500; font-size:.92rem;}
  .al.do {background:#FDECEA; border-left:5px solid #DC3545;} .al.vang {background:#FFF6E0; border-left:5px solid #F0A500;} .al.xanh {background:#EAF5EA; border-left:5px solid #28A745;}
  .sbox {border-radius:10px; padding:18px; color:#fff; position:relative; min-height:110px;}
  .sbox .n {font-size:1.9rem; font-weight:800; color:#fff;} .sbox .t {font-size:.95rem; color:#fff; opacity:.92;}
  .sbox .ic {position:absolute; right:16px; top:12px; font-size:2.4rem; opacity:.35;}
  .hero {background:linear-gradient(120deg,#1F4E79 0%,#2B6CB0 60%,#E07A1F 140%); border-radius:14px; padding:34px 36px; color:#fff;}
  .hero h1 {color:#fff; font-size:2.2rem; margin:0 0 8px 0; padding:0;} .hero p {color:#EAF1F8; font-size:1.02rem; margin:0;}
  .flowx {display:grid; grid-template-columns:repeat(8,1fr); gap:8px; margin-top:6px;}
  .flowx div { background:#F4F6F9; border:1px solid #E3E7EC; border-radius:8px; padding:10px; text-align:center; font-size:.85rem; font-weight:600; color:#1F2D3D;}
  .flowx div span {display:block; font-size:1.2rem; font-weight:800; color:#1F6FEB;}
  .sug {border:1px solid #E3E7EC; border-left:5px solid #1F6FEB; border-radius:8px; padding:12px 14px; background:#FFFFFF;}
  .sug b {color:#1F2D3D;} .sug p {font-size:.86rem; color:#6C757D; margin:4px 0 0 0;}
  .authbox {max-width:440px; margin:6vh auto 0 auto;}
  .stTabs [data-baseweb="tab-list"] {gap:4px;}
</style>""", unsafe_allow_html=True)

ss = st.session_state
ss.setdefault("S", P.new_state())
ss.setdefault("user", None)
ss.setdefault("page", "home")
ss.setdefault("unlocked", 1)       # bước cao nhất được phép mở
ss.setdefault("finished", False)
S = ss.S
S.setdefault("extras", [])
ss.setdefault("prefs", {"theme": TH.AUTO, "dark": False, "motion": True, "custom": {"primary": "#0F766E", "accent": "#14B8A6"}})
_pf = ss.prefs
_label, _t = TH.resolve(_pf["theme"], _pf.get("custom"))
st.markdown(TH.css(_pf["theme"], _pf["dark"], _pf["motion"], _pf.get("custom")), unsafe_allow_html=True)
D.set_palette(_t["primary"], _t["accent"], _pf["dark"])
CP_MSG = {
    3: "⚠️ <b>TRẠM KIỂM SOÁT BƯỚC 3 · LÀM SẠCH DỮ LIỆU</b>: quá trình làm sạch đã hoàn tất nhưng có điểm cần anh/chị duyệt.",
    4: "⚠️ <b>TRẠM KIỂM SOÁT BƯỚC 4 · TIỀN XỬ LÝ</b>: phát hiện rủi ro kỹ thuật cần xem xét.",
    5: "⚠️ <b>TRẠM KIỂM SOÁT BƯỚC 5 · KIỂM ĐỊNH KẾT QUẢ</b>: kết quả thống kê hoặc mô hình chưa đạt độ tin cậy yêu cầu.",
    6: "⚠️ <b>TRẠM KIỂM SOÁT BƯỚC 6 · BÁO CÁO ĐIỀU HÀNH</b>: bản báo cáo còn điểm chưa đạt chuẩn trình bày.",
    7: "⚠️ <b>TRẠM KIỂM SOÁT BƯỚC 7 · KẾT LUẬN VÀ ĐỀ XUẤT</b>: kế hoạch hành động còn thiếu thông tin bắt buộc.",
    8: "⚠️ <b>TRẠM KIỂM SOÁT BƯỚC 8 · XUẤT TỆP</b>: bản thảo chưa đạt chuẩn xuất bản.",
}
CP_ASK = {
    3: "👉 Phê duyệt để chuyển sang bước khám phá dữ liệu, hoặc ghi chỉ dẫn điều chỉnh phương pháp làm sạch (ví dụ: 'xoá các dòng vi phạm logic', 'giữ nguyên cột X')?",
    4: "👉 Phê duyệt để tiếp tục, hoặc ghi chỉ dẫn: rút gọn biến, đổi biến mục tiêu, loại biến nghi rò rỉ.",
    5: "👉 Chấp nhận kết quả kèm cảnh báo, hoặc ghi chỉ dẫn đổi biến mục tiêu, loại bớt biến.",
    6: "👉 Phê duyệt để sang bước đề xuất, hoặc ghi chỉ dẫn chỉnh biểu đồ, văn phong báo cáo.",
    7: "👉 Phê duyệt kế hoạch, hoặc ghi chỉ dẫn bổ sung người phụ trách, thời hạn, chỉ tiêu và nhóm việc làm ngay.",
    8: "👉 Bạn muốn bổ sung nội dung, hay xuất báo cáo với hiện trạng?",
}



def friendly_error(raw: str) -> str:
    """Ẩn chuỗi lỗi kỹ thuật, chỉ hiển thị hướng xử lý."""
    r = raw.lower()
    if "api key" in r or "api_key" in r or "unauthenticated" in r or "access_token" in r or "permission" in r:
        return "🔑 Khóa truy cập Gemini chưa hợp lệ. Vui lòng tạo khóa mới tại aistudio.google.com/apikey rồi dán lại vào ô bên trên. Trong lúc chờ, hệ thống vẫn chạy bằng quy tắc có sẵn."
    if "quota" in r or "429" in r or "resource_exhausted" in r:
        return "⏳ Khóa truy cập đã dùng hết hạn mức tạm thời. Vui lòng thử lại sau ít phút."
    if "timeout" in r or "connect" in r or "network" in r or "unavailable" in r or "503" in r:
        return "🌐 Không kết nối được tới máy chủ Gemini. Vui lòng kiểm tra mạng Internet."
    if "not found" in r or "404" in r:
        return "🧩 Phiên bản mô hình không tồn tại. Vui lòng kiểm tra lại tên mô hình, ví dụ gemini-2.5-flash."
    return "⚠️ Dịch vụ Gemini tạm thời chưa phản hồi. Hệ thống vẫn tiếp tục bằng quy tắc có sẵn."


def status_badge(n: int):
    stt = S["statuses"].get(n)
    if stt == "PASS":
        nxt = f"sang Bước {n + 1}" if n < 8 else "xem kết quả cuối cùng"
        st.markdown(f"<div class='ok'>✅ <b>Kết quả kiểm soát: Đạt</b> — bấm xác nhận để {nxt}.</div>", unsafe_allow_html=True)
    elif stt:
        st.markdown("**Kết quả kiểm soát:** Cần người duyệt")


_KEY = [0]


def _next_key():
    _KEY[0] += 1
    return _KEY[0]


def show_charts(section_filter=None, cols=2):
    ch = [c for c in S["charts"] if section_filter is None or c["section"] in section_filter]
    grid = st.columns(cols)
    for i, c in enumerate(ch):
        with grid[i % cols]:
            fig = interactive(c, S)
            if fig is not None:
                st.plotly_chart(fig, width="stretch", config={"displaylogo": False}, key=f"pl_{c['id']}_{_next_key()}")
                st.caption(c["caption"].replace("Hình: ", ""))
            else:
                st.image(c["path"], caption=c["caption"], width="stretch")
            lead = S.get("story", {}).get("chart_leads", {}).get(c["id"])
            if lead:
                st.caption("💬 " + lead)


# ------------------------------------------------------------ render từng bước
def render1():
    st.markdown(S["biz_md"])


ISSUE_TYPE = {"missing_critical": "Thiếu dữ liệu nghiêm trọng", "wrong_dtype": "Sai định dạng", "negative_values": "Giá trị âm bất thường",
              "outliers": "Giá trị ngoại lệ", "future_dates": "Ngày ở tương lai", "duplicates": "Dòng trùng lặp", "logic": "Vi phạm logic nghiệp vụ"}
SEVERITY = {"high": "Cao", "medium": "Trung bình", "low": "Thấp"}
TYPE_VI = {"numeric": "Số", "numeric_as_text": "Số lưu dạng chữ", "datetime": "Ngày tháng", "datetime_as_text": "Ngày lưu dạng chữ",
           "categorical": "Phân loại", "text": "Văn bản", "id": "Mã định danh", "boolean": "Đúng/Sai", "empty": "Trống"}
MODEL_VI = {"RandomForestRegressor": "Rừng ngẫu nhiên (dự báo giá trị)", "RandomForestClassifier": "Rừng ngẫu nhiên (phân loại)"}
METRIC_VI = {"r2": "Mức giải thích biến động (0–1)", "rmse": "Sai số trung bình bình phương", "mae": "Sai số tuyệt đối trung bình",
             "accuracy": "Tỷ lệ dự đoán đúng", "f1_macro": "Điểm cân bằng chính xác", "roc_auc": "Khả năng phân biệt nhãn"}
TEST_VI = {"Kruskal-Wallis": "So sánh nhiều nhóm", "Spearman": "Tương quan thứ hạng", "Chi-square": "Kiểm định độc lập"}


def render2():
    pr = S["prof"]
    ov = pr["overview"]
    c = st.columns(5)
    c[0].metric("Số dòng", f"{ov['rows']:,}".replace(",", "."))
    c[1].metric("Số cột", ov["columns"])
    c[2].metric("Dung lượng", f"{ov['memory_mb']:.2f} MB".replace(".", ","))
    c[3].metric("Dòng trùng lặp", ov["duplicates"])
    c[4].metric("Điểm chất lượng", f"{pr['quality_score']}/10".replace(".", ","))
    st.markdown(f"**Đánh giá rủi ro:** {pr['risk_comment']}")
    st.markdown("##### Báo cáo kiểm định chất lượng dữ liệu: các điểm bất thường về định dạng và logic")
    if pr["issues"]:
        t = pd.DataFrame(pr["issues"]).rename(columns={"column": "Cột", "type": "Loại bất thường", "severity": "Mức độ", "detail": "Chi tiết"})
        t["Loại bất thường"] = t["Loại bất thường"].map(ISSUE_TYPE).fillna(t["Loại bất thường"])
        t["Mức độ"] = t["Mức độ"].map(SEVERITY)
        st.dataframe(t, width="stretch", hide_index=True)
    else:
        st.success("Không phát hiện điểm bất thường đáng kể.")
    with st.expander("📋 Cấu trúc và thống kê từng cột"):
        t = pd.DataFrame(pr["columns"]).drop(columns=["sample", "pandas_dtype"], errors="ignore")
        t["inferred_type"] = t["inferred_type"].map(TYPE_VI)
        t = t.rename(columns={"column": "Cột", "inferred_type": "Kiểu dữ liệu", "missing": "Số ô trống", "missing_pct": "Tỷ lệ trống (%)",
                              "unique": "Số giá trị khác nhau", "mean": "Trung bình", "median": "Trung vị", "min": "Nhỏ nhất", "max": "Lớn nhất",
                              "outliers_iqr": "Số ngoại lệ", "negatives": "Số giá trị âm", "unparseable": "Không chuyển đổi được",
                              "min_date": "Ngày sớm nhất", "max_date": "Ngày muộn nhất", "future_dates": "Ngày tương lai"})
        st.dataframe(t, width="stretch", hide_index=True)
    st.markdown("##### Nhận định rủi ro nghiệp vụ")
    st.markdown(S["prof_comment"])


def render3():
    cl = S["clean"]
    c = st.columns(4)
    c[0].metric("Số dòng trước làm sạch", f"{cl['rows_before']:,}".replace(",", "."))
    c[1].metric("Số dòng sau làm sạch", f"{cl['rows_after']:,}".replace(",", "."))
    c[2].metric("Tỷ lệ dòng bị loại", f"{cl['data_loss_percentage']}%".replace(".", ","))
    c[3].metric("Số ô được điền bổ sung", f"{cl['imputed_cells']:,}".replace(",", "."))
    st.markdown("**Nhật ký làm sạch**")
    st.markdown("\n".join(f"- {x}" for x in cl["cleaning_action_log"]) or "- Không cần thao tác làm sạch.")
    if cl["logic_checks"]:
        st.markdown("**Kiểm tra luật nghiệp vụ**")
        t = pd.DataFrame(cl["logic_checks"])[["rule", "violations"]].rename(columns={"rule": "Luật", "violations": "Số dòng vi phạm"})
        st.dataframe(t, width="stretch", hide_index=True)
    if cl["distribution_shift"]:
        st.markdown("**Kiểm tra sai lệch phân phối trước và sau khi điền bổ sung**")
        t = pd.DataFrame(cl["distribution_shift"]).rename(columns={"column": "Cột", "mean_before": "Trung bình trước", "mean_after": "Trung bình sau",
                                                                    "median_before": "Trung vị trước", "median_after": "Trung vị sau",
                                                                    "mean_change_pct": "Lệch trung bình (%)", "median_change_pct": "Lệch trung vị (%)", "flag": "Vượt ngưỡng 15%"})
        st.dataframe(t, width="stretch", hide_index=True)
    with st.expander("Xem trước dữ liệu sạch"):
        st.dataframe(cl["df"].head(50), width="stretch")
        st.download_button("⬇️ Tải dữ liệu sạch (CSV)", cl["df"].to_csv(index=False).encode("utf-8-sig"), "du_lieu_sach.csv", "text/csv")


def render4():
    mp, pp = S["mplan"], S["pp_summary"]
    st.markdown(f"**Thiết lập phân tích:** biến mục tiêu `{mp['target']}` · chỉ số chính `{mp['kpi']}` · cột thời gian `{mp['date_col']}` · "
                f"phân khúc so sánh: {', '.join(mp['segment_cols']) or 'không có'}")
    st.markdown("##### Khám phá dữ liệu")
    show_charts({2, 3})
    st.markdown("**Nhật ký tiền xử lý**")
    st.markdown("\n".join(f"- {x}" for x in pp["preprocessing_log"]))
    for w in pp.get("warnings", []):
        st.info(w)
    lk, ib, dm = pp.get("leakage_check"), pp.get("imbalance_check"), pp.get("dimensionality_check")
    c = st.columns(3)
    if lk:
        sus = lk.get("suspicious_features") or []
        c[0].markdown("**Rò rỉ dữ liệu**  \n" + ("Chuẩn hóa chỉ dựa trên tập học: " + ("đạt" if lk.get("scaler_fit_on_train_only") else "chưa đạt")) +
                      "  \n" + (f"Biến đáng ngờ: {', '.join(f['feature'] for f in sus)}" if sus else "Không có biến đáng ngờ"))
    if ib:
        c[1].markdown(f"**Cân bằng nhãn**  \nTrước: {ib['before']}  \nSau: {ib['after']}")
    if dm:
        c[2].markdown(f"**Số chiều dữ liệu**  \n{dm['cols_before']} biến gốc → {dm['cols_after']} cột sau mã hóa  \nTỷ lệ cột/dòng: {dm['ratio']}")


def render5():
    an = S["analysis"]
    if an["metrics"]:
        m = an["metrics"]
        st.markdown(f"**Mô hình:** {MODEL_VI.get(m['model'], m['model'])} · biến mục tiêu `{an['outcome']}`")
        t = pd.DataFrame({"Tập học": m["train"], "Tập kiểm tra": m["test"], "Mô hình đối chứng": m["baseline_test"]})
        t.index = [METRIC_VI.get(i, i) for i in t.index]
        st.dataframe(t, width="stretch")
    if an["metric_tree"]:
        mt = an["metric_tree"]
        comp = " · ".join(f"{k}: {v:+.1f}%" for k, v in mt["components"].items())
        st.markdown(f"**Phân rã chỉ số:** {an['kpi']} = Số giao dịch × Giá trị trung bình mỗi giao dịch → tổng thay đổi "
                    f"**{mt['total_change_pct']:+.1f}%** ({comp}). Yếu tố chính: **{mt['main_driver']}**.")
    show_charts({4})
    if an["tests"]:
        with st.expander(f"Kiểm định thống kê: {sum(t['significant'] for t in an['tests'])}/{len(an['tests'])} yếu tố có ý nghĩa"):
            t = pd.DataFrame(an["tests"])[["feature", "test", "p_adj", "significant"]]
            t["test"] = t["test"].map(TEST_VI).fillna(t["test"])
            t = t.rename(columns={"feature": "Yếu tố", "test": "Phép kiểm định", "p_adj": "Xác suất ngẫu nhiên (đã hiệu chỉnh)", "significant": "Có ý nghĩa (độ tin cậy 95%)"})
            st.dataframe(t, width="stretch", hide_index=True)
    st.markdown("##### Nhận định chính")
    for i in an["insights"]:
        st.markdown(f"- **{i.get('insight', '')}**  \n  _Bằng chứng:_ {i.get('evidence', '')}  \n  _Hành động gợi ý:_ {i.get('action_hint', '')}")
    if an.get("validation_report"):
        st.markdown(f"**Đánh giá độ tin cậy:** {an['validation_report']}")
    for f in an["validation"]["flags"]:
        st.warning(f)


def render6():
    es = S["story"]["executive_summary"]
    st.markdown(f"#### 🎯 {es.get('headline', '')}")
    st.markdown("\n".join(f"- {k}" for k in es.get("key_points", [])))
    if es.get("top_recommendation"):
        st.markdown(f"**Khuyến nghị ưu tiên:** {es['top_recommendation']}")
    with st.expander("Biểu đồ kèm diễn giải"):
        show_charts()
    st.markdown("**Kết quả rà soát trình bày**")
    st.markdown("\n".join(f"- {x}" for x in S["viz_audit"]["visualization_audit_log"]))


def render7():
    pl = S["plan"]
    cols = {"what": "Hành động", "why": "Lý do", "who": "Người phụ trách", "when": "Thời hạn", "where": "Phạm vi", "how": "Cách thực hiện",
            "kpi": "Chỉ tiêu", "impact": "Tác động", "effort": "Nguồn lực"}
    lv = {"H": "Cao", "M": "Trung bình", "L": "Thấp"}
    for h, label in HORIZONS.items():
        acts = [a for a in pl.get("actions", []) if a.get("horizon") == h]
        if acts:
            st.markdown(f"##### {label}")
            t = pd.DataFrame(acts)[[c for c in cols if c in acts[0]]]
            for c in ("impact", "effort"):
                if c in t:
                    t[c] = t[c].astype(str).str[:1].str.upper().map(lv).fillna(t[c])
            st.dataframe(t.rename(columns=cols), width="stretch", hide_index=True)
    if pl.get("risks"):
        st.markdown("##### Rủi ro và phương án dự phòng")
        st.dataframe(pd.DataFrame(pl["risks"]).rename(columns={"risk": "Rủi ro", "mitigation": "Phương án dự phòng"}), width="stretch", hide_index=True)
    if pl.get("limitations"):
        st.markdown("**Hạn chế của phân tích:** " + "; ".join(pl["limitations"]))
    st.markdown("**Rà soát kế hoạch:** " + " · ".join(S["plan_audit"]["strategic_audit_report"]))


def render8():
    st.markdown("**Kết quả rà soát trước khi xuất bản**")
    st.markdown("\n".join(f"- {x}" for x in S["export"]["report_readiness_summary"]))


RENDER = {1: render1, 2: render2, 3: render3, 4: render4, 5: render5, 6: render6, 7: render7, 8: render8}


def _fmt(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    a = abs(v)
    s = f"{v/1e9:,.2f} tỷ" if a >= 1e9 else f"{v/1e6:,.1f} triệu" if a >= 1e6 else f"{v:,.0f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def vn_table(t: pd.DataFrame) -> pd.DataFrame:
    """Định dạng số kiểu Việt Nam: dấu chấm phân cách nghìn, dấu phẩy thập phân."""
    t = t.copy()
    for c in t.columns:
        if pd.api.types.is_numeric_dtype(t[c]):
            dec = 2 if "%" in str(c) else 0
            t[c] = t[c].map(lambda v: "—" if pd.isna(v) else f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", "."))
    return t


def render_dashboard():
    """Bảng điều khiển 2 tầng: Tầng I tính toán, Tầng II trực quan."""
    df, types, mp = S["clean"]["df"], S["clean"]["types"], S["mplan"]
    p = D.build_params(df, mp, types)
    if not p["kpi"]:
        st.info("Dữ liệu không có cột số phù hợp làm chỉ số chính, nên chưa dựng được bảng điều khiển.")
        return
    # ---- Khu vực tiêu đề & bộ lọc
    st.markdown(f"### Bảng điều khiển {p['kpi']}")
    f = st.columns([2] + [1] * min(2, len(p["segments"])))
    rng = None
    if p.get("date_col"):
        a, b = p["ngay_dau"].date(), p["ngay_cuoi"].date()
        rng = f[0].date_input("Khoảng thời gian", (a, b), min_value=a, max_value=b, format="DD/MM/YYYY")
        if not isinstance(rng, (tuple, list)) or len(rng) != 2:
            rng = (a, b)
    segf = {}
    for i, s in enumerate(p["segments"][:2], 1):
        segf[s] = f[i].multiselect(s, sorted(df[s].dropna().astype(str).unique()), placeholder="Tất cả")
    d = D.apply_filters(df, p, rng, segf)
    if d.empty:
        st.warning("Không có dữ liệu trong phạm vi lọc đã chọn.")
        return
    tables = D.summary_tables(d, p)
    kt = D.kpi_table(d, p, tables)
    desc = []
    if rng:
        desc.append(f"từ {rng[0]:%d/%m/%Y} đến {rng[1]:%d/%m/%Y}")
    desc += [f"{k}: {', '.join(v)}" for k, v in segf.items() if v]
    ss.dash_state = {"d": d, "p": p, "tables": tables, "kpi_table": kt, "alerts": D.alerts(tables, p),
                     "filter_desc": "; ".join(desc) or "toàn bộ dữ liệu"}
    # ---- Khu vực thẻ chỉ số
    cards = kt[kt["Giá trị"].notna()].head(5)
    cs = st.columns(len(cards))
    for col, (_, r) in zip(cs, cards.iterrows()):
        chg = r["Thay đổi (%)"]
        cls, arrow = ("flat", "") if chg is None or pd.isna(chg) else (("up", "▲") if chg >= 0 else ("down", "▼"))
        dtxt = f"{arrow} {chg:+.1f}%".replace(".", ",") + f" · {r['Ghi chú'].lower()}" if cls != "flat" else r["Ghi chú"]
        col.markdown(f"<div class='kpi'><div class='lb'>{r['Chỉ số']}</div><div class='v'>{_fmt(r['Giá trị'])}</div><div class='d {cls}'>{dtxt}</div></div>", unsafe_allow_html=True)
    st.write("")
    # ---- Khu vực biểu đồ chính
    seg = p["segments"][0] if p["segments"] else None
    c1, c2 = st.columns([3, 2])
    if "theo_thang" in tables:
        c1.plotly_chart(D.fig_trend(tables["theo_thang"], p["kpi"]), width="stretch", config={"displaylogo": False}, key="db_trend")
    if seg:
        c2.plotly_chart(D.fig_donut(tables[f"theo_{seg}"], seg), width="stretch", config={"displaylogo": False}, key="db_donut")
    c3, c4 = st.columns([3, 2])
    seg2 = p["segments"][1] if len(p["segments"]) > 1 else seg
    if seg2:
        c3.plotly_chart(D.fig_bar(tables[f"theo_{seg2}"], seg2), width="stretch", config={"displaylogo": False}, key="db_bar")
    # ---- Khu vực cảnh báo
    with c4:
        st.markdown("**Vùng cảnh báo**")
        for a in D.alerts(tables, p):
            st.markdown(f"<div class='al {a['muc']}'>{a['noi_dung']}</div>", unsafe_allow_html=True)
    # ---- Chi tiết
    if seg2:
        t = tables[f"theo_{seg2}"]
        st.markdown(f"**Nhóm dẫn đầu và nhóm thấp nhất theo {seg2}**")
        st.dataframe(vn_table(pd.concat([t.head(3), t.tail(3)]).drop_duplicates()), width="stretch")
    # ---- Tầng I: phần tính toán
    with st.expander("Tầng tính toán: bảng chỉ số, bảng tổng hợp, tham số và dữ liệu nguồn"):
        st.markdown("**Bảng chỉ số cốt lõi**")
        st.dataframe(vn_table(kt), width="stretch", hide_index=True)
        for k, t in tables.items():
            st.markdown(f"**Bảng tổng hợp {k.replace('theo_', 'theo ').replace('_', ' ')}**")
            st.dataframe(vn_table(t), width="stretch")
        st.markdown("**Bảng tham số**")
        st.dataframe(pd.DataFrame([
            ["Cột thời gian", p["date_col"]], ["Chỉ số chính", p["kpi"]], ["Phân khúc", ", ".join(p["segments"])],
            ["Kỳ so sánh", "Tháng gần nhất so với tháng liền trước"], ["Ngưỡng cảnh báo đỏ", f"Giảm từ {abs(p['nguong_giam_do']):.0f}% trở lên"],
            ["Ngưỡng cảnh báo vàng", "Giảm dưới 10%"]], columns=["Tham số", "Giá trị"]), width="stretch", hide_index=True)
        st.markdown(f"**Dữ liệu nguồn đã lọc** ({len(d):,} dòng)".replace(",", "."))
        st.dataframe(d.head(200), width="stretch")


DASH_ITEMS = {"the_chi_so": "Thẻ chỉ số cốt lõi", "xu_huong": "Biểu đồ xu hướng theo thời gian", "so_sanh": "Biểu đồ so sánh các nhóm",
              "co_cau": "Cơ cấu tỷ trọng theo nhóm", "canh_bao": "Vùng cảnh báo", "bang_tong_hop": "Bảng tổng hợp số liệu"}


def _dash_bundle(opts: set) -> dict | None:
    """Gói dữ liệu bảng điều khiển (đúng bộ lọc hiện tại) thành biểu đồ tĩnh để chèn vào Word/PDF."""
    from core import charts as C
    ds = ss.get("dash_state")
    if not ds:
        return None
    d, p = ds["d"], ds["p"]
    out_dir = os.path.join(S["out_dir"], "dash")
    os.makedirs(out_dir, exist_ok=True)
    agg = "sum"
    items = []
    if "xu_huong" in opts and p.get("date_col"):
        c = C.trend(d, p["date_col"], p["kpi"], out_dir, agg)
        if c:
            f = c["facts"]
            items.append({"key": "xu_huong", "path": c["path"], "caption": f"{p['kpi']} theo {f['freq']} ({ds['filter_desc']})",
                          "lead": f"Trong phạm vi đã lọc, {p['kpi']} đạt đỉnh vào {f['peak']} và thấp nhất vào {f['low']}; "
                                  f"trung bình nửa sau giai đoạn thay đổi {f['half_over_half_change_pct']}% so với nửa đầu."})
    segs = p.get("segments", [])
    if "co_cau" in opts and segs:
        c = C.category_bar(d, segs[0], p["kpi"], out_dir, agg)
        sh = c["facts"].get("share_pct") or {}
        top = next(iter(sh.items()), ("", 0))
        items.append({"key": "co_cau", "path": c["path"], "caption": f"Cơ cấu {p['kpi']} theo {segs[0]}",
                      "lead": f"Nhóm {top[0]} chiếm tỷ trọng lớn nhất với {top[1]}% {p['kpi']} theo {segs[0]}."})
    if "so_sanh" in opts and len(segs) > 1:
        c = C.category_bar(d, segs[1], p["kpi"], out_dir, agg)
        v = c["facts"]["values"]
        hi, lo = list(v.items())[0], list(v.items())[-1]
        items.append({"key": "so_sanh", "path": c["path"], "caption": f"So sánh {p['kpi']} theo {segs[1]}",
                      "lead": f"Theo {segs[1]}, nhóm {hi[0]} dẫn đầu, nhóm {lo[0]} thấp nhất; chênh lệch {hi[1] / lo[1]:.1f} lần." if lo[1] else f"So sánh {p['kpi']} theo {segs[1]}."})
    return {**ds, "kpi": p["kpi"], "charts": items}


def report_builder():
    """Người dùng tự chọn nội dung báo cáo; Word/PDF được dựng theo đúng lựa chọn và bộ lọc bảng điều khiển."""
    from core import report as REP
    st.markdown("#### 🧩 Tùy chỉnh nội dung báo cáo")
    st.caption("Chọn những phần bạn cần. Phần bảng điều khiển sẽ dùng đúng bộ lọc bạn đang đặt ở tab Bảng điều khiển.")
    with st.form("report_form"):
        c1, c2 = st.columns(2)
        title = c1.text_input("Tiêu đề báo cáo", "Báo cáo Phân tích Dữ liệu Kinh doanh")
        author = c2.text_input("Người lập / Đơn vị", "")
        st.markdown("**Các phần nội dung**")
        cols = st.columns(4)
        picked = set()
        defaults = {"tomtat", "dashboard", "nguyennhan", "dexuat"} | ({"bosung"} if S.get("extras") else set())
        for i, (k, label) in enumerate(REP.SECTION_KEYS.items()):
            if cols[i % 4].checkbox(label, value=k in defaults, key=f"sec_{k}"):
                picked.add(k)
        dash_opts = set(st.multiselect("Nội dung lấy từ bảng điều khiển", list(DASH_ITEMS), default=list(DASH_ITEMS)[:5],
                                       format_func=DASH_ITEMS.get, disabled=False))
        if ss.get("dash_state"):
            st.caption(f"Phạm vi dữ liệu hiện tại: {ss.dash_state['filter_desc']}")
        go = st.form_submit_button("📄 Tạo báo cáo", type="primary", width="stretch")
    if go:
        if not picked:
            st.warning("Vui lòng chọn ít nhất một phần nội dung.")
            return
        with st.spinner("Đang dựng báo cáo theo lựa chọn của bạn…"):
            bundle = _dash_bundle(dash_opts) if "dashboard" in picked else None
            ss.custom_export = REP.build_and_validate(S, os.path.join(S["out_dir"], "export_custom"), picked, bundle, dash_opts,
                                                      {"title": title.strip(), "author": author.strip()})
            ss.custom_export["picked"] = [REP.SECTION_KEYS[k] for k in REP.SECTION_KEYS if k in picked]
    ex = ss.get("custom_export")
    if ex:
        st.markdown(f"<div class='export'><b>✅ Báo cáo đã sẵn sàng</b> — gồm: {', '.join(ex['picked'])}.</div>", unsafe_allow_html=True)
        for r in ex["reasons"]:
            st.warning(r)
        d1, d2 = st.columns(2)
        with open(ex["docx"], "rb") as f:
            d1.download_button("📄 Tải báo cáo Word", f.read(), os.path.basename(ex["docx"]),
                               "application/vnd.openxmlformats-officedocument.wordprocessingml.document", width="stretch", type="primary")
        with open(ex["pdf"], "rb") as f:
            d2.download_button("📑 Tải báo cáo PDF", f.read(), os.path.basename(ex["pdf"]), "application/pdf", width="stretch", type="primary")


def export_widget():
    ex = S["export"]
    st.markdown("<div class='export'>", unsafe_allow_html=True)
    st.markdown("#### ✅ Báo cáo phân tích đã sẵn sàng\n"
                "- 5 phần chuẩn: tóm tắt điều hành, hiện trạng dữ liệu, khám phá dữ liệu, nguyên nhân gốc rễ, đề xuất và lộ trình\n"
                "- Biểu đồ đã qua rà soát tính trung thực, mỗi hình có diễn giải và chú thích\n"
                "- Kế hoạch hành động có người phụ trách, thời hạn và chỉ tiêu đo được")
    c1, c2 = st.columns(2)
    with open(ex["docx"], "rb") as f:
        c1.download_button("📄 Tải báo cáo Word", f.read(), os.path.basename(ex["docx"]),
                           "application/vnd.openxmlformats-officedocument.wordprocessingml.document", width="stretch", type="primary")
    with open(ex["pdf"], "rb") as f:
        c2.download_button("📑 Tải báo cáo PDF", f.read(), os.path.basename(ex["pdf"]), "application/pdf", width="stretch", type="primary")
    st.markdown("</div>", unsafe_allow_html=True)




_BOX = [0]


def box():
    """Thẻ nội dung có khóa riêng để CSS chủ đề tô nền ổn định."""
    _BOX[0] += 1
    return st.container(border=True, key=f"card_{_BOX[0]}")


# ================================================================== ĐĂNG NHẬP / ĐĂNG KÝ
def auth_page():
    st.markdown("<style>[data-testid='stSidebar'],[data-testid='stSidebarCollapsedControl']{display:none;}</style>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1.1, 1])
    with mid:
        st.markdown("<div style='text-align:center;margin-top:5vh'><div style='font-size:2.6rem'>📊</div>"
                    "<h2 style='margin:4px 0 2px 0'>Phân tích Dữ liệu Kinh doanh</h2>"
                    "<p style='color:#6C757D;margin:0 0 16px 0'>Đăng nhập để bắt đầu phiên phân tích</p></div>", unsafe_allow_html=True)
        with box():
            t1, t2 = st.tabs(["Đăng nhập", "Đăng ký"])
            with t1:
                with st.form("login"):
                    u = st.text_input("Tên đăng nhập")
                    p = st.text_input("Mật khẩu", type="password")
                    if st.form_submit_button("Đăng nhập", type="primary", width="stretch"):
                        user = auth.login(u, p)
                        if user:
                            ss.user = user
                            saved = auth.get_prefs(user["username"])
                            if saved:
                                ss.prefs = {**ss.prefs, **saved}
                            ss.page = "home"
                            st.rerun()
                        st.error("Tên đăng nhập hoặc mật khẩu không đúng.")
            with t2:
                with st.form("register"):
                    fn = st.text_input("Họ và tên")
                    u2 = st.text_input("Tên đăng nhập", help="3–32 ký tự: chữ không dấu, số, dấu chấm, gạch dưới")
                    p2 = st.text_input("Mật khẩu", type="password", help="Tối thiểu 6 ký tự")
                    p3 = st.text_input("Nhập lại mật khẩu", type="password")
                    if st.form_submit_button("Tạo tài khoản", type="primary", width="stretch"):
                        if p2 != p3:
                            st.error("Mật khẩu nhập lại không khớp.")
                        else:
                            ok, msg = auth.register(u2, p2, fn)
                            (st.success if ok else st.error)(msg)
        st.caption("Tài khoản được lưu trên máy chủ chạy ứng dụng; mật khẩu được mã hóa một chiều.")


if not ss.user:
    auth_page()
    st.stop()


# ================================================================== THANH BÊN
PAGES = [("home", "🏠", "Giới thiệu")] + [(f"s{n}", "", f"{n}. {name}") for n, name in P.STEP_NAMES.items()] + [("results", "📊", "Kết quả và báo cáo")]


def page_allowed(pid: str) -> bool:
    if pid == "home":
        return True
    if pid == "results":
        return ss.finished
    return int(pid[1:]) <= ss.unlocked


def go(pid: str):
    ss.page = pid
    st.rerun()


with st.sidebar:
    st.markdown("<div class='brand'><div class='lg'>P</div><b>Phân tích Dữ liệu</b></div>", unsafe_allow_html=True)
    nm = ss.user["fullname"]
    st.markdown(f"<div class='user'><div class='av'>{nm[:1].upper()}</div><span>{nm}</span></div>", unsafe_allow_html=True)
    st.markdown("<div class='sec'>Điều hướng</div>", unsafe_allow_html=True)
    for pid, ic, label in PAGES:
        if pid.startswith("s"):
            n = int(pid[1:])
            done = S["statuses"].get(n) == "PASS" or (n < ss.unlocked) or (n == 8 and ss.finished)
            ic = "✅" if done and n < ss.unlocked or (n == 8 and ss.finished) else ("🟠" if n == ss.unlocked else "○")
        if st.button(f"{ic}  {label}", key=f"nav_{pid}", width="stretch", disabled=not page_allowed(pid),
                     type="primary" if ss.page == pid else "secondary"):
            go(pid)
    st.markdown("<div class='sec'>Hệ thống</div>", unsafe_allow_html=True)
    with st.expander(f"🎨 Giao diện · {_t['icon']} {_label}", expanded=False):
        opts = [TH.AUTO] + list(TH.THEMES) + [TH.CUSTOM]
        th = st.selectbox("Chủ đề", opts, index=opts.index(_pf["theme"]) if _pf["theme"] in opts else 0,
                          format_func=lambda o: f"{TH.THEMES[o]['icon']} {o}" if o in TH.THEMES else ("📅 " + o + f" ({TH.seasonal()})" if o == TH.AUTO else "🎨 " + o))
        dk = st.toggle("🌙 Chế độ tối", value=_pf["dark"])
        mo = st.toggle("✨ Nền động", value=_pf["motion"], help="Tắt nếu muốn giao diện tĩnh hoàn toàn")
        cu = dict(_pf.get("custom") or {})
        if th == TH.CUSTOM:
            c1, c2 = st.columns(2)
            cu["primary"] = c1.color_picker("Màu chủ đạo", cu.get("primary", "#0F766E"))
            cu["accent"] = c2.color_picker("Màu nhấn", cu.get("accent", "#14B8A6"))
        new = {"theme": th, "dark": dk, "motion": mo, "custom": cu}
        if new != _pf:
            ss.prefs = new
            auth.save_prefs(ss.user["username"], new)
            st.rerun()
    with st.expander("⚙️ Cài đặt mô hình", expanded=False):
        api_key = st.text_input("Khóa truy cập Gemini", value=os.getenv("GEMINI_API_KEY", ""), type="password")
        model = st.text_input("Phiên bản mô hình", value=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    key = (api_key, model)
    if ss.get("llm_key") != key:
        ss.llm, ss.llm_key = LLMClient(api_key, model), key
    llm: LLMClient = ss.llm
    st.caption("🟢 Đã cấu hình Gemini" if not llm.mock else "⚪ Chế độ ngoại tuyến (chưa có khóa)")
    if S["logs"]:
        st.download_button("⬇️ Nhật ký xử lý", json.dumps(S["logs"], ensure_ascii=False, default=str, indent=2), "nhat_ky.json", "application/json", width="stretch")
    c1, c2 = st.columns(2)
    if c1.button("🔄 Phiên mới", width="stretch"):
        for k in ("S", "unlocked", "finished", "custom_export", "dash_state", "sugs"):
            ss.pop(k, None)
        ss.page = "s1"
        st.rerun()
    if c2.button("⎋ Đăng xuất", width="stretch"):
        for k in list(ss.keys()):
            del ss[k]
        st.rerun()

if llm.last_error and not llm.mock:
    st.toast(friendly_error(llm.last_error), icon="⚠️")


# ================================================================== TIỆN ÍCH
def topbar(title: str, crumb: str):
    st.markdown(f"<div class='topbar'><h2>{title}</h2><div class='crumb'>Trang chủ / <b>{crumb}</b></div></div>", unsafe_allow_html=True)


def card_header(title: str, sub: str = ""):
    st.markdown(f"<div class='cardh'>{title}</div>" + (f"<div class='cardsub'>{sub}</div>" if sub else ""), unsafe_allow_html=True)


def run_step(n: int, feedback: str | None = None) -> bool:
    """Chạy đúng một bước; lỗi được hiển thị thân thiện."""
    with st.status(f"Đang xử lý Bước {n}: {P.STEP_NAMES[n]}…", expanded=False) as box:
        try:
            P.STEPS[n](S, llm, feedback)
        except Exception as exc:
            box.update(label="Quá trình xử lý bị gián đoạn", state="error")
            st.error("Hệ thống chưa hoàn tất bước này. Vui lòng kiểm tra lại dữ liệu hoặc ghi chỉ dẫn điều chỉnh rồi chạy lại.")
            with st.expander("Chi tiết kỹ thuật (dành cho quản trị viên)"):
                st.code(f"{type(exc).__name__}: {str(exc)[:500]}")
            return False
        box.update(label=f"Hoàn tất Bước {n}", state="complete")
    return True


def invalidate_after(n: int):
    """Chạy lại bước n thì các bước sau phải làm lại."""
    for k in list(S["statuses"]):
        if k > n:
            S["statuses"].pop(k)
    ss.unlocked, ss.finished = n, False
    ss.pop("custom_export", None)


def confirm_bar(n: int):
    """Thanh xác nhận cuối mỗi trang bước."""
    is_front = n == ss.unlocked and not (n == 8 and ss.finished)
    with box():
        if S["statuses"].get(n) == "PASS":
            st.markdown(f"<div class='ok'>✅ <b>Bước {n} đạt các tiêu chí kiểm soát.</b> Vui lòng xem kết quả rồi xác nhận.</div>", unsafe_allow_html=True)
        else:
            summ = next((l["summary"] for l in reversed(S["logs"]) if l["step"] == n), {})
            reasons = (summ.get("reasons") or summ.get("validation", {}).get("flags", [])) if isinstance(summ, dict) else []
            st.markdown(f"<div class='cp'>{CP_MSG[n]}<br>" + "".join(f"• {r}<br>" for r in reasons) + f"{CP_ASK[n]}</div>", unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1])
        if is_front:
            nxt = f"✅ Xác nhận & sang Bước {n + 1}" if n < 8 else "✅ Xác nhận & xem kết quả"
            if c1.button(nxt, type="primary", width="stretch", key=f"cf{n}"):
                if n == 8:
                    ss.finished = True
                    go("results")
                if run_step(n + 1):
                    ss.unlocked = n + 1
                    go(f"s{n + 1}")
        else:
            c1.info("Bạn đang xem lại bước đã hoàn thành.")
        with c2.popover(f"🔁 Chạy lại Bước {n} với chỉ dẫn", width="stretch"):
            fb = st.text_area("Chỉ dẫn điều chỉnh", key=f"fb{n}", placeholder="Ví dụ: giữ nguyên cột discount_code, xoá các dòng vi phạm logic…")
            if st.button("Chạy lại", key=f"rr{n}", type="primary", disabled=not fb.strip()):
                invalidate_after(n)
                if run_step(n, fb):
                    go(f"s{n}")


# ================================================================== TRANG LÀM SẠCH: XEM, LỌC, SỬA
def clean_editor():
    df = S["clean"]["df"]
    types = S["clean"]["types"]
    with box():
        card_header("Dữ liệu sau làm sạch", f"{len(df):,} dòng × {df.shape[1]} cột · lọc để kiểm tra, sửa trực tiếp rồi bấm Lưu".replace(",", "."))
        f1, f2 = st.columns([2, 3])
        q = f1.text_input("🔎 Tìm nhanh trong mọi cột", key="ce_q")
        cols = f2.multiselect("Lọc theo cột", list(df.columns), key="ce_cols", placeholder="Chọn cột cần lọc")
        mask = pd.Series(True, index=df.index)
        if cols:
            fc = st.columns(min(3, len(cols)))
            for i, c in enumerate(cols):
                holder = fc[i % len(fc)]
                s = df[c]
                if pd.api.types.is_datetime64_any_dtype(s) and s.notna().any():
                    a, b = s.min().date(), s.max().date()
                    r = holder.date_input(c, (a, b), min_value=a, max_value=b, key=f"ce_d_{c}", format="DD/MM/YYYY")
                    if isinstance(r, (list, tuple)) and len(r) == 2:
                        mask &= s.between(pd.Timestamp(r[0]), pd.Timestamp(r[1]) + pd.Timedelta(days=1))
                elif pd.api.types.is_numeric_dtype(s) and s.nunique() > 12:
                    lo, hi = float(s.min()), float(s.max())
                    if lo < hi:
                        r = holder.slider(c, lo, hi, (lo, hi), key=f"ce_n_{c}")
                        mask &= s.between(*r) | s.isna()
                else:
                    opts = sorted(s.dropna().astype(str).unique())[:300]
                    v = holder.multiselect(c, opts, key=f"ce_c_{c}", placeholder="Tất cả")
                    if v:
                        mask &= s.astype(str).isin(v)
        if q:
            mask &= df.astype(str).apply(lambda col: col.str.contains(q, case=False, na=False)).any(axis=1)
        view = df[mask]
        st.caption(f"Đang hiển thị {len(view):,} / {len(df):,} dòng".replace(",", "."))
        cfg = {c: st.column_config.DatetimeColumn(c, format="DD/MM/YYYY") for c, t in types.items() if t == "datetime" and c in df}
        edited = st.data_editor(view, key="ce_editor", width="stretch", height=420, num_rows="fixed", column_config=cfg)
        if st.button("💾 Lưu chỉnh sửa", type="primary"):
            diff = (edited != view) & ~(edited.isna() & view.isna())
            n = int(diff.values.sum())
            if n == 0:
                st.info("Không có ô nào thay đổi.")
            else:
                S["clean"]["df"].loc[edited.index, edited.columns] = edited
                S["clean"]["cleaning_action_log"].append(f"Người dùng chỉnh sửa thủ công {n} ô dữ liệu")
                if ss.unlocked > 3 or ss.finished:
                    invalidate_after(3)
                    st.warning("Dữ liệu đã thay đổi nên các bước từ Bước 4 trở đi cần chạy lại. Bấm xác nhận để tiếp tục.")
                st.success(f"Đã lưu {n} ô thay đổi.")
                st.rerun()


# ================================================================== GỢI Ý PHÂN TÍCH BỔ SUNG
def suggestions_panel(key_prefix: str):
    with box():
        card_header("💡 Gợi ý phân tích thêm cho nhà quản trị", "Các hướng phân tích có thể bổ sung giá trị; bấm để thực hiện và đưa vào báo cáo")
        sugs = SG.build(S)
        if not sugs:
            st.caption("Đã thực hiện hết các gợi ý phù hợp với dữ liệu hiện tại.")
        for i in range(0, len(sugs), 2):
            cols = st.columns(2)
            for c, sg in zip(cols, sugs[i:i + 2]):
                with c:
                    st.markdown(f"<div class='sug'><b>{sg['title']}</b><p>{sg['why']}</p></div>", unsafe_allow_html=True)
                    if st.button("▶ Phân tích", key=f"{key_prefix}_{sg['id']}", width="stretch"):
                        try:
                            S["extras"].append(SG.run(S, sg))
                        except Exception:
                            st.error("Không thực hiện được phân tích này với dữ liệu hiện tại.")
                        st.rerun()
    for j, e in enumerate(S["extras"]):
        with box():
            h1, h2 = st.columns([6, 1])
            h1.markdown(f"<div class='cardh'>{e['title']}</div>", unsafe_allow_html=True)
            if h2.button("✕ Bỏ", key=f"{key_prefix}_rm{j}"):
                S["extras"].pop(j)
                st.rerun()
            if e.get("fig") is not None:
                st.plotly_chart(e["fig"], width="stretch", config={"displaylogo": False}, key=f"{key_prefix}_fx{j}")
            st.markdown(f"**Nhận xét:** {e['note']}")
            if e.get("table") is not None:
                with st.expander("Bảng số liệu"):
                    st.dataframe(vn_table(e["table"]), width="stretch")


# ================================================================== CÁC TRANG
page = ss.page if page_allowed(ss.page) else "home"

if page == "home":
    topbar("Giới thiệu", "Giới thiệu")
    st.markdown(f"""<div class='hero'><h1>Xin chào, {ss.user['fullname']} 👋</h1>
<p>Ứng dụng giúp bạn đi từ dữ liệu bán hàng thô đến nguyên nhân, đề xuất và báo cáo chỉ trong một quy trình 8 bước.
Mọi con số được tính trực tiếp từ dữ liệu; bạn xác nhận kết quả sau mỗi bước.</p></div>""", unsafe_allow_html=True)
    st.write("")
    c = st.columns(3)
    boxes = [("#1F6FEB", "🧭", "8 bước", "Quy trình phân tích chuẩn hóa"), ("#28A745", "🛡️", "Từng bước", "Bạn xác nhận trước khi đi tiếp"),
             ("#E07A1F", "📄", "Word · PDF", "Báo cáo theo nội dung bạn chọn")]
    for col, (bg, ic, n, t) in zip(c, boxes):
        col.markdown(f"<div class='sbox' style='background:{bg}'><div class='ic'>{ic}</div><div class='n'>{n}</div><div class='t'>{t}</div></div>", unsafe_allow_html=True)
    st.write("")
    with box():
        card_header("Quy trình làm việc", "Mỗi bước nằm ở một trang riêng trên thanh điều hướng bên trái")
        st.markdown("<div class='flowx'>" + "".join(f"<div><span>{n}</span>{name}</div>" for n, name in P.STEP_NAMES.items()) + "</div>", unsafe_allow_html=True)
    with box():
        card_header("Bạn cần chuẩn bị")
        a, b = st.columns(2)
        a.markdown("**1. Mô tả doanh nghiệp**  \nLĩnh vực, quy mô, mục tiêu, chỉ số quan tâm, giai đoạn và thị trường.")
        b.markdown("**2. Tệp dữ liệu**  \nCSV hoặc Excel, mỗi dòng là một giao dịch, có cột ngày và cột giá trị.")
    if st.button("🚀 Bắt đầu phân tích", type="primary"):
        go("s1" if ss.unlocked <= 1 else f"s{ss.unlocked}")

elif page == "s1":
    topbar("Bước 1 · Tiếp nhận bối cảnh", "Bước 1")
    if "biz" not in S or ss.get("edit1"):
        with box():
            card_header("Mô tả doanh nghiệp", "Viết theo từng dòng để hệ thống tóm tắt chính xác hơn")
            txt = st.text_area("Nội dung", height=200, label_visibility="collapsed", value=S.get("user_text", ""),
                               placeholder="Tên doanh nghiệp\nLĩnh vực: …\nQuy mô: …\nMục tiêu: …\nChỉ số quan tâm: …\nGiai đoạn: …\nThị trường: …")
            with st.expander("📎 Đính kèm tài liệu nội bộ (tuỳ chọn)"):
                docs = st.file_uploader("PDF, Word, PowerPoint, TXT", type=["pdf", "docx", "pptx", "txt", "md"], accept_multiple_files=True)
            if st.button("🔍 Phân tích bối cảnh", type="primary", disabled=not txt.strip() and not docs):
                with st.spinner("Đang tóm tắt bối cảnh…"):
                    dtext = "\n\n".join(f"=== {d.name} ===\n{extract_text(d.name, d.getvalue())}" for d in (docs or []))
                    P.step1(S, llm, txt, dtext)
                ss.edit1 = False
                invalidate_after(1)
                st.rerun()
    else:
        with box():
            card_header("Hồ sơ bối cảnh doanh nghiệp")
            render1()
        with box():
            c1, c2, c3 = st.columns(3)
            if c1.button("✅ Xác nhận & sang Bước 2", type="primary", width="stretch"):
                ss.unlocked = max(ss.unlocked, 2)
                go("s2")
            with c2.popover("✏️ Yêu cầu chỉnh sửa", width="stretch"):
                fb = st.text_area("Nội dung cần sửa", key="fb1")
                if st.button("Cập nhật hồ sơ", disabled=not fb.strip()):
                    P.step1(S, llm, S["user_text"], S["docs_text"], feedback=fb)
                    invalidate_after(1)
                    st.rerun()
            if c3.button("📝 Nhập lại mô tả", width="stretch"):
                ss.edit1 = True
                st.rerun()

elif page == "s2":
    topbar("Bước 2 · Đánh giá chất lượng dữ liệu", "Bước 2")
    if "prof" not in S or ss.get("reupload"):
        with box():
            card_header("Tải lên dữ liệu thô", "CSV hoặc Excel, tối đa 200 MB")
            up = st.file_uploader("Tệp dữ liệu", type=["csv", "xlsx", "xls", "xlsm"], label_visibility="collapsed")
            if up and st.button("🧪 Quét chất lượng dữ liệu", type="primary"):
                with st.spinner("Đang quét dữ liệu…"):
                    try:
                        P.step2(S, llm, up.name, up.getvalue())
                    except Exception:
                        st.error("Không đọc được tệp. Vui lòng kiểm tra định dạng CSV hoặc Excel.")
                        st.stop()
                ss.reupload = False
                invalidate_after(2)
                st.rerun()
    else:
        with box():
            card_header("Báo cáo kiểm định chất lượng dữ liệu", S.get("raw_name", ""))
            render2()
        with box():
            notes = st.text_area("Lưu ý nghiệp vụ cho bước làm sạch (tuỳ chọn)", value=S["feedback"].get(2, ""),
                                 placeholder="Ví dụ: cột discount_code được phép để trống")
            c1, c2 = st.columns(2)
            if ss.unlocked == 2:
                if c1.button("✅ Xác nhận & sang Bước 3", type="primary", width="stretch"):
                    S["feedback"][2] = notes
                    if run_step(3):
                        ss.unlocked = 3
                        go("s3")
            else:
                c1.info("Bạn đang xem lại bước đã hoàn thành.")
            if c2.button("📤 Tải tệp khác", width="stretch"):
                ss.reupload = True
                st.rerun()

elif page.startswith("s"):
    n = int(page[1:])
    topbar(f"Bước {n} · {P.STEP_NAMES[n]}", f"Bước {n}")
    if n not in S["statuses"]:
        st.info("Bước này chưa được chạy. Hãy xác nhận bước trước để tiếp tục.")
    else:
        if n == 3:
            t1, t2 = st.tabs(["📋 Tóm tắt làm sạch", "🗂️ Xem, lọc và chỉnh sửa dữ liệu"])
            with t1:
                with box():
                    RENDER[3]()
            with t2:
                clean_editor()
        elif n == 5:
            with box():
                RENDER[5]()
            suggestions_panel("s5")
        else:
            with box():
                RENDER[n]()
        confirm_bar(n)

elif page == "results":
    topbar("Kết quả và báo cáo", "Kết quả")
    t1, t2, t3 = st.tabs(["📊 Bảng điều khiển", "💡 Phân tích bổ sung", "📄 Báo cáo"])
    with t1:
        with box():
            render_dashboard()
    with t2:
        suggestions_panel("res")
    with t3:
        with box():
            report_builder()
        with st.expander("Tóm tắt điều hành và kết quả rà soát"):
            if S.get("story"):
                render6()
            render8()
