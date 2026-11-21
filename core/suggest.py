"""Gợi ý phân tích bổ sung cho nhà quản trị: đề xuất hướng phân tích mới, chạy khi người dùng chọn."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from . import dashboard as DB
from .dashboard import GREY, _layout, money, money_axis, vn

WEEKDAY = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]


def _cats(df: pd.DataFrame, types: dict, exclude: list) -> list[str]:
    return [c for c, t in types.items() if t in ("categorical", "boolean") and c not in exclude and 2 <= df[c].nunique() <= 30]


def build(S: dict) -> list[dict]:
    """Sinh danh sách gợi ý dựa trên dữ liệu và kết quả đã có; ưu tiên yếu tố có ý nghĩa thống kê."""
    df, types, mp = S["clean"]["df"], S["clean"]["types"], S["mplan"]
    kpi, dc = mp.get("kpi"), mp.get("date_col")
    if not kpi:
        return []
    an = S.get("analysis", {})
    sig = [t["feature"] for t in an.get("tests", []) if t.get("significant")]
    cats = _cats(df, types, mp.get("exclude", []))
    cats = sorted(cats, key=lambda c: (c not in sig, c in mp.get("segment_cols", [])[:2]))
    nums = [c for c, t in types.items() if t == "numeric" and c != kpi and c not in mp.get("exclude", []) and df[c].nunique() > 3]
    out = []
    for c in cats[:2]:
        note = "Yếu tố này có ý nghĩa thống kê ở bước phân tích chuyên sâu." if c in sig else "Nhóm này chưa được xem chi tiết trên bảng điều khiển."
        out.append({"id": f"breakdown:{c}", "kind": "breakdown", "col": c, "title": f"Cơ cấu {kpi} và giá trị đơn trung bình theo {c}", "why": note})
    if dc:
        out.append({"id": "weekday", "kind": "weekday", "title": f"{kpi} theo ngày trong tuần", "why": "Giúp bố trí nhân sự, khuyến mãi và quảng cáo theo ngày cao điểm."})
    if cats:
        c = max(cats, key=lambda x: df[x].nunique())
        out.append({"id": f"pareto:{c}", "kind": "pareto", "col": c, "title": f"Nhóm {c} nào tạo ra phần lớn {kpi} (nguyên tắc 80/20)",
                    "why": "Xác định nhóm trọng điểm để tập trung nguồn lực."})
    if dc and cats:
        out.append({"id": f"segtrend:{cats[0]}", "kind": "segtrend", "col": cats[0], "title": f"Xu hướng {kpi} theo tháng của từng nhóm {cats[0]}",
                    "why": "Phát hiện nhóm đang tăng trưởng hoặc suy giảm, điều mà số tổng có thể che khuất."})
    if len(cats) >= 2:
        out.append({"id": f"cross:{cats[0]}:{cats[1]}", "kind": "cross", "col": cats[0], "col2": cats[1],
                    "title": f"Ma trận {kpi} theo {cats[0]} và {cats[1]}", "why": "Tìm tổ hợp hiệu quả nhất và kém nhất giữa hai chiều phân tích."})
    for n in nums[:2]:
        why = "Yếu tố có ý nghĩa thống kê." if n in sig else "Kiểm tra xem biến số này có đi cùng chiều với chỉ số chính không."
        out.append({"id": f"relation:{n}", "kind": "relation", "col": n, "title": f"Mối liên hệ giữa {n} và {kpi}", "why": why})
    done = {e["id"] for e in S.get("extras", [])}
    return [s for s in out if s["id"] not in done][:6]


def run(S: dict, sug: dict) -> dict:
    """Thực hiện một gợi ý: trả về biểu đồ Plotly, bảng số liệu và nhận xét tính bằng mã."""
    df, mp = S["clean"]["df"], S["mplan"]
    kpi, dc = mp["kpi"], mp.get("date_col")
    k, c = sug["kind"], sug.get("col")
    fig, table, note = None, None, ""
    if k == "breakdown":
        g = df.groupby(c, observed=True)[kpi].agg(["sum", "count", "mean"]).sort_values("sum", ascending=False)
        g["share"] = 100 * g["sum"] / g["sum"].sum()
        fig = go.Figure()
        fig.add_bar(x=g.index.astype(str), y=g["sum"], name="Tổng", marker_color=DB.NAVY, customdata=np.stack([g["share"], g["mean"]], -1),
                    hovertemplate="<b>%{x}</b><br>Tổng: %{y:,.0f}<br>Tỷ trọng: %{customdata[0]:.1f}%<br>Giá trị TB/đơn: %{customdata[1]:,.0f}<extra></extra>")
        money_axis(fig, float(g["sum"].max()))
        fig = _layout(fig, sug["title"])
        top, low = g.index[0], g.index[-1]
        note = (f"Nhóm “{top}” dẫn đầu với {vn(g['share'].iloc[0])}% {kpi}, giá trị trung bình mỗi đơn {money(g['mean'].iloc[0])}. "
                f"Nhóm “{low}” thấp nhất ({vn(g['share'].iloc[-1])}%).")
        table = g.rename(columns={"sum": "Tổng", "count": "Số đơn", "mean": "Giá trị TB/đơn", "share": "Tỷ trọng (%)"})
    elif k == "weekday":
        w = df.assign(_d=df[dc].dt.dayofweek).groupby("_d")[kpi].agg(["sum", "count"]).reindex(range(7), fill_value=0)
        w.index = WEEKDAY
        best, worst = w["sum"].idxmax(), w["sum"].idxmin()
        fig = go.Figure(go.Bar(x=w.index, y=w["sum"], marker_color=[DB.ORANGE if i == best else DB.NAVY for i in w.index], customdata=w["count"],
                               hovertemplate="<b>%{x}</b><br>Tổng: %{y:,.0f}<br>Số đơn: %{customdata:,}<extra></extra>"))
        money_axis(fig, float(w["sum"].max()))
        fig = _layout(fig, sug["title"])
        gap = 100 * (w["sum"].max() - w["sum"].min()) / w["sum"].min() if w["sum"].min() else 0
        note = f"{best} có {kpi} cao nhất, {worst} thấp nhất; chênh lệch {vn(gap)}%."
        table = w.rename(columns={"sum": "Tổng", "count": "Số đơn"})
    elif k == "pareto":
        g = df.groupby(c, observed=True)[kpi].sum().sort_values(ascending=False)
        cum = 100 * g.cumsum() / g.sum()
        n80 = int((cum < 80).sum() + 1)
        fig = go.Figure()
        fig.add_bar(x=g.index.astype(str), y=g.values, marker_color=DB.NAVY, name="Giá trị", hovertemplate="<b>%{x}</b><br>%{y:,.0f}<extra></extra>")
        fig.add_scatter(x=g.index.astype(str), y=cum.values, yaxis="y2", mode="lines+markers", line=dict(color=DB.ORANGE, width=3), name="Lũy kế (%)",
                        hovertemplate="Lũy kế: %{y:.1f}%<extra></extra>")
        fig = _layout(fig, sug["title"])
        fig.update_layout(yaxis2=dict(overlaying="y", side="right", range=[0, 105], ticksuffix="%", showgrid=False))
        note = f"{n80}/{len(g)} nhóm ({vn(100 * n80 / len(g))}%) tạo ra 80% {kpi}."
        table = pd.DataFrame({"Giá trị": g, "Lũy kế (%)": cum})
    elif k == "segtrend":
        p = df.pivot_table(index=pd.Grouper(key=dc, freq="MS"), columns=c, values=kpi, aggfunc="sum", observed=True).fillna(0)
        p.index = p.index.strftime("%m/%Y")
        palette = [DB.NAVY, DB.ORANGE, "#4F7CAC", "#F2B880", GREY, "#2E7D32", "#7C3AED"]
        fig = go.Figure()
        for i, col in enumerate(p.columns[:7]):
            fig.add_scatter(x=p.index, y=p[col], mode="lines+markers", name=str(col), line=dict(color=palette[i % 7], width=2.5),
                            hovertemplate=f"<b>{col}</b> · %{{x}}<br>%{{y:,.0f}}<extra></extra>")
        fig = _layout(fig, sug["title"])
        fig.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.15))
        half = len(p) // 2
        chg = (100 * (p.iloc[half:].mean() - p.iloc[:half].mean()) / p.iloc[:half].mean().replace(0, np.nan)).dropna().sort_values()
        if len(chg):
            note = f"So với nửa đầu giai đoạn: “{chg.index[-1]}” thay đổi {vn(chg.iloc[-1])}%, “{chg.index[0]}” thay đổi {vn(chg.iloc[0])}%."
        table = p
    elif k == "cross":
        c2 = sug["col2"]
        p = df.pivot_table(index=c, columns=c2, values=kpi, aggfunc="sum", observed=True).fillna(0)
        fig = go.Figure(go.Heatmap(z=p.values, x=p.columns.astype(str), y=p.index.astype(str), colorscale="Blues",
                                   hovertemplate="%{y} × %{x}<br>%{z:,.0f}<extra></extra>"))
        fig = _layout(fig, sug["title"], 420)
        st = p.stack()
        note = f"Tổ hợp cao nhất: {st.idxmax()[0]} × {st.idxmax()[1]} ({money(st.max())}); thấp nhất: {st.idxmin()[0]} × {st.idxmin()[1]} ({money(st.min())})."
        table = p
    elif k == "relation":
        d = df[[c, kpi]].dropna()
        try:
            bins = pd.qcut(d[c], q=min(5, d[c].nunique()), duplicates="drop")
        except ValueError:
            bins = d[c]
        g = d.groupby(bins, observed=True)[kpi].agg(["mean", "count"])
        g.index = g.index.astype(str)
        r = d[c].corr(d[kpi], method="spearman")
        fig = go.Figure(go.Bar(x=g.index, y=g["mean"], marker_color=DB.NAVY, customdata=g["count"],
                               hovertemplate=f"{c}: %{{x}}<br>{kpi} TB: %{{y:,.0f}}<br>Số đơn: %{{customdata:,}}<extra></extra>"))
        fig = _layout(fig, sug["title"])
        strength = "mạnh" if abs(r) >= 0.5 else "vừa" if abs(r) >= 0.3 else "yếu"
        note = f"Mức tương quan {vn(r, 2)} ({strength}, {'cùng chiều' if r > 0 else 'ngược chiều'}): {kpi} trung bình thay đổi theo các khoảng {c} như biểu đồ."
        table = g.rename(columns={"mean": f"{kpi} trung bình", "count": "Số đơn"})
    return {"id": sug["id"], "title": sug["title"], "fig": fig, "table": table, "note": note}
