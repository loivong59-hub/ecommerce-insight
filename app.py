import re
import unicodedata

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# ----------------------------------------------------------------------------
# Cấu hình trang
# ----------------------------------------------------------------------------
st.set_page_config(page_title="Ecom Insight", page_icon="📊", layout="wide")

st.markdown(
    """
<style>
[data-testid="stMetric"] {
    background: rgba(128,128,128,0.08);
    padding: 16px; border-radius: 12px;
    border: 1px solid rgba(128,128,128,0.25);
}
.block-container {padding-top: 1.5rem;}
</style>
""",
    unsafe_allow_html=True,
)

COLORS = px.colors.qualitative.Set2


# ----------------------------------------------------------------------------
# Hàm tiện ích hiển thị
# ----------------------------------------------------------------------------
def money(x):
    return f"{x:,.0f} đ".replace(",", ".")


def short_money(x):
    if abs(x) >= 1e9:
        return f"{x / 1e9:.2f} tỷ".replace(".", ",")
    if abs(x) >= 1e6:
        return f"{x / 1e6:.1f} triệu".replace(".", ",")
    return money(x)


def show_chart(fig):
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=10), legend_title_text="")
    try:
        st.plotly_chart(fig, width="stretch")
    except TypeError:  # Streamlit bản cũ
        st.plotly_chart(fig, use_container_width=True)


def show_table(df):
    try:
        st.dataframe(df, width="stretch", hide_index=True)
    except TypeError:
        st.dataframe(df, use_container_width=True, hide_index=True)


# ----------------------------------------------------------------------------
# Dữ liệu mẫu
# ----------------------------------------------------------------------------
@st.cache_data
def sample_data():
    rng = np.random.default_rng(42)
    products = {
        "Tai nghe Bluetooth": ("Điện tử", 450000),
        "Áo thun": ("Thời trang", 180000),
        "Bình giữ nhiệt": ("Gia dụng", 220000),
        "Chuột không dây": ("Điện tử", 250000),
        "Giày thể thao": ("Thời trang", 650000),
        "Balo laptop": ("Phụ kiện", 390000),
        "Ốp điện thoại": ("Phụ kiện", 90000),
        "Đèn bàn": ("Gia dụng", 280000),
    }
    customers = [
        "Nguyễn Minh Anh", "Trần Gia Huy", "Lê Hoàng Yến", "Phạm Tuấn Kiệt",
        "Võ Ngọc Hà", "Đặng Quốc Bảo", "Bùi Thanh Tâm", "Huỳnh Đức Long",
        "Đỗ Khánh Linh", "Phan Nhật Nam", "Mai Phương Thảo", "Ngô Anh Tú",
    ]
    channels = ["Shopee", "TikTok Shop", "Website", "Facebook"]
    statuses = ["Hoàn thành", "Đang giao", "Đã hủy"]
    start = pd.Timestamp.today().normalize() - pd.Timedelta(days=179)
    names = list(products.keys())
    rows = []
    for i in range(300):
        product = str(rng.choice(names))
        category, price = products[product]
        rows.append(
            {
                "Ma_don_hang": f"DH{i + 1:04d}",
                "Ngay_dat": start + pd.Timedelta(days=int(rng.integers(0, 180))),
                "Khach_hang": str(rng.choice(customers)),
                "San_pham": product,
                "Danh_muc": category,
                "So_luong": int(rng.choice([1, 1, 1, 2, 2, 3])),
                "Don_gia": price,
                "Giam_gia": int(rng.choice([0, 0, 0, 10000, 20000, 30000])),
                "Kenh_ban": str(rng.choice(channels, p=[0.4, 0.3, 0.15, 0.15])),
                "Trang_thai": str(rng.choice(statuses, p=[0.72, 0.12, 0.16])),
            }
        )
    df = pd.DataFrame(rows)
    df["Doanh_thu"] = (df["So_luong"] * df["Don_gia"] - df["Giam_gia"]).clip(lower=0)
    return df


# ----------------------------------------------------------------------------
# Đọc và chuẩn hóa CSV
# ----------------------------------------------------------------------------
ALIASES = {
    "Ma_don_hang": ["ma_don_hang", "ma_don", "order_id", "id"],
    "Ngay_dat": ["ngay_dat", "ngay", "ngay_dat_hang", "ngay_mua", "order_date", "date"],
    "Khach_hang": ["khach_hang", "ten_khach_hang", "ten_kh", "khach", "customer", "customer_name"],
    "San_pham": ["san_pham", "ten_san_pham", "ten_hang", "product", "product_name", "item"],
    "So_luong": ["so_luong", "sl", "quantity", "qty"],
    "Don_gia": ["don_gia", "gia", "gia_ban", "price", "unit_price"],
    "Giam_gia": ["giam_gia", "chiet_khau", "discount"],
    "Danh_muc": ["danh_muc", "nhom_hang", "loai", "category"],
    "Kenh_ban": ["kenh_ban", "kenh", "nen_tang", "channel"],
    "Trang_thai": ["trang_thai", "tinh_trang", "status"],
}
REQUIRED = ["Ngay_dat", "Khach_hang", "San_pham", "So_luong", "Don_gia"]


def norm_col(s):
    s = str(s).replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def standardize_columns(df):
    lookup = {a: canon for canon, names in ALIASES.items() for a in names}
    rename = {}
    for col in df.columns:
        key = norm_col(col)
        if key in lookup and lookup[key] not in rename.values():
            rename[col] = lookup[key]
    return df.rename(columns=rename)


def to_number(series):
    """Đổi cột sang số, chấp nhận dạng '1.250.000' hoặc '1,250,000 đ'."""
    if series.dtype == object:
        series = series.astype(str).str.replace(r"[^\d,.\-]", "", regex=True)
        has_dot_thousand = series.str.match(r"^-?\d{1,3}(\.\d{3})+$")
        has_comma_thousand = series.str.match(r"^-?\d{1,3}(,\d{3})+$")
        series = series.where(~has_dot_thousand, series.str.replace(".", "", regex=False))
        series = series.where(~has_comma_thousand, series.str.replace(",", "", regex=False))
        series = series.str.replace(",", ".", regex=False)
    return pd.to_numeric(series, errors="coerce")


def prepare_data(df):
    df = standardize_columns(df.copy())
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        st.error("File CSV thiếu cột: " + ", ".join(missing))
        st.write("Các cột app đọc được trong file của bạn:", list(df.columns))
        st.caption(
            "Đặt tên cột như file mẫu (Ngay_dat, Khach_hang, San_pham, So_luong, Don_gia) "
            "hoặc dùng tên gần giống như 'Ngày đặt', 'Khách hàng', 'Số lượng'."
        )
        st.stop()

    df["Ngay_dat"] = pd.to_datetime(df["Ngay_dat"], errors="coerce", dayfirst=True)
    df["So_luong"] = to_number(df["So_luong"]).fillna(0)
    df["Don_gia"] = to_number(df["Don_gia"]).fillna(0)
    if "Giam_gia" not in df.columns:
        df["Giam_gia"] = 0
    df["Giam_gia"] = to_number(df["Giam_gia"]).fillna(0)
    for col, default in [
        ("Ma_don_hang", None),
        ("Danh_muc", "Chưa phân loại"),
        ("Kenh_ban", "Không xác định"),
        ("Trang_thai", "Hoàn thành"),
    ]:
        if col not in df.columns:
            df[col] = default if default is not None else [f"DH{i + 1:04d}" for i in range(len(df))]
        elif default is not None:
            df[col] = df[col].fillna(default).astype(str)

    df = df.dropna(subset=["Ngay_dat", "Khach_hang", "San_pham"])
    if df.empty:
        st.error("Không có dòng dữ liệu hợp lệ (kiểm tra lại cột ngày và các ô bị trống).")
        st.stop()
    df["Doanh_thu"] = (df["So_luong"] * df["Don_gia"] - df["Giam_gia"]).clip(lower=0)
    return df


def read_csv_smart(file):
    for enc in ("utf-8-sig", "cp1258", "latin-1"):
        try:
            file.seek(0)
            return pd.read_csv(file, sep=None, engine="python", encoding=enc)
        except UnicodeDecodeError:
            continue
    raise ValueError("Không đọc được bảng mã của file CSV")


def is_cancelled(series):
    return series.astype(str).str.lower().str.contains(r"hủy|huỷ|huy|cancel|hoàn trả|return", regex=True)


# ----------------------------------------------------------------------------
# 1) Nạp dữ liệu
# ----------------------------------------------------------------------------
st.sidebar.title("📊 Ecom Insight")
st.sidebar.caption("Phân tích kinh doanh thương mại điện tử")

uploaded = st.sidebar.file_uploader("Tải dữ liệu đơn hàng CSV", type=["csv"])
st.sidebar.download_button(
    "⬇️ Tải file CSV mẫu",
    sample_data().head(30).drop(columns=["Doanh_thu"]).to_csv(index=False).encode("utf-8-sig"),
    file_name="don_hang_mau.csv",
    mime="text/csv",
)

if uploaded is not None:
    try:
        data = prepare_data(read_csv_smart(uploaded))
        st.sidebar.success(f"Đã tải {len(data):,} đơn hàng của bạn.".replace(",", "."))
    except Exception as error:
        st.sidebar.error(f"Không đọc được CSV: {error}")
        st.stop()
else:
    data = sample_data()
    st.sidebar.info("Đang dùng 300 đơn hàng mẫu.")

data = data.copy()
data["Huy"] = is_cancelled(data["Trang_thai"])

# ----------------------------------------------------------------------------
# 2) Bộ lọc
# ----------------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("Bộ lọc")

min_d, max_d = data["Ngay_dat"].min().date(), data["Ngay_dat"].max().date()
date_range = st.sidebar.date_input(
    "Khoảng ngày", value=(min_d, max_d), min_value=min_d, max_value=max_d
)
if isinstance(date_range, (tuple, list)):
    if len(date_range) == 2:
        d_from, d_to = date_range
    elif len(date_range) == 1:
        d_from = d_to = date_range[0]
    else:
        d_from, d_to = min_d, max_d
else:
    d_from = d_to = date_range

channels = sorted(data["Kenh_ban"].unique())
cats = sorted(data["Danh_muc"].unique())
stats = sorted(data["Trang_thai"].unique())
sel_channels = st.sidebar.multiselect("Kênh bán", channels, default=channels)
sel_cats = st.sidebar.multiselect("Danh mục", cats, default=cats)
sel_stats = st.sidebar.multiselect("Trạng thái", stats, default=stats)
granularity = st.sidebar.radio("Xem doanh thu theo", ["Ngày", "Tuần", "Tháng"], index=2, horizontal=True)

base = data[
    data["Kenh_ban"].isin(sel_channels)
    & data["Danh_muc"].isin(sel_cats)
    & data["Trang_thai"].isin(sel_stats)
]
start_ts, end_ts = pd.Timestamp(d_from), pd.Timestamp(d_to) + pd.Timedelta(days=1)
df = base[(base["Ngay_dat"] >= start_ts) & (base["Ngay_dat"] < end_ts)]

if df.empty:
    st.title("📊 Ecom Insight")
    st.warning("Không có đơn hàng nào khớp bộ lọc. Hãy nới rộng bộ lọc ở thanh bên.")
    st.stop()

sales = df[~df["Huy"]]  # chỉ tính doanh thu cho đơn không bị hủy

# kỳ trước (cùng độ dài) để so sánh
days = max((end_ts - start_ts).days, 1)
prev_df = base[(base["Ngay_dat"] >= start_ts - pd.Timedelta(days=days)) & (base["Ngay_dat"] < start_ts)]
prev_sales = prev_df[~prev_df["Huy"]]


def delta_pct(cur, prev):
    if prev and prev > 0:
        return f"{(cur - prev) / prev * 100:+.1f}% so với kỳ trước"
    return None


# ----------------------------------------------------------------------------
# 3) Giao diện chính
# ----------------------------------------------------------------------------
st.title("📊 Ecom Insight")
st.caption(f"Dữ liệu từ {d_from:%d/%m/%Y} đến {d_to:%d/%m/%Y} · Doanh thu không tính đơn đã hủy")

revenue = sales["Doanh_thu"].sum()
orders = len(sales)
aov = revenue / orders if orders else 0
cancel_rate = df["Huy"].mean() * 100
customers_n = sales["Khach_hang"].nunique()

prev_rev = prev_sales["Doanh_thu"].sum()
prev_orders = len(prev_sales)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Doanh thu", short_money(revenue), delta_pct(revenue, prev_rev))
c2.metric("Số đơn hợp lệ", f"{orders:,}".replace(",", "."), delta_pct(orders, prev_orders))
c3.metric("Giá trị đơn TB", money(aov))
c4.metric("Tỷ lệ hủy", f"{cancel_rate:.1f}%")
c5.metric("Khách hàng", customers_n)

tab1, tab2, tab3, tab4 = st.tabs(["📈 Tổng quan", "🛍️ Sản phẩm", "👥 Khách hàng", "🗂️ Dữ liệu"])

# ---------------- Tab Tổng quan ----------------
with tab1:
    if sales.empty:
        st.info("Tất cả đơn trong khoảng đã chọn đều bị hủy nên chưa có doanh thu.")
    else:
        freq = {"Ngày": "D", "Tuần": "W", "Tháng": "M"}[granularity]
        period = sales["Ngay_dat"].dt.to_period(freq).dt.start_time
        trend = sales.groupby(period).agg(Doanh_thu=("Doanh_thu", "sum"), So_don=("Doanh_thu", "size")).reset_index()
        trend.columns = ["Thời gian", "Doanh thu", "Số đơn"]

        if granularity == "Ngày":
            fig = px.line(trend, x="Thời gian", y="Doanh thu", markers=False, title="Doanh thu theo ngày")
        else:
            fig = px.bar(trend, x="Thời gian", y="Doanh thu", title=f"Doanh thu theo {granularity.lower()}")
        if granularity != "Ngày":
            fig.update_traces(marker_color=COLORS[0])
        fig.update_yaxes(tickformat=",.0f")
        show_chart(fig)

        left, right = st.columns(2)
        with left:
            by_ch = sales.groupby("Kenh_ban")["Doanh_thu"].sum().reset_index()
            fig = px.pie(by_ch, names="Kenh_ban", values="Doanh_thu", hole=0.5,
                         title="Doanh thu theo kênh bán", color_discrete_sequence=COLORS)
            show_chart(fig)
        with right:
            by_cat = sales.groupby("Danh_muc")["Doanh_thu"].sum().reset_index().sort_values("Doanh_thu")
            fig = px.bar(by_cat, x="Doanh_thu", y="Danh_muc", orientation="h",
                         title="Doanh thu theo danh mục", labels={"Doanh_thu": "Doanh thu", "Danh_muc": ""})
            fig.update_traces(marker_color=COLORS[1])
            fig.update_xaxes(tickformat=",.0f")
            show_chart(fig)

    st.subheader("Trạng thái đơn hàng")
    by_status = df.groupby("Trang_thai").size().reset_index(name="So_don")
    fig = px.bar(by_status, x="Trang_thai", y="So_don", text="So_don",
                 labels={"Trang_thai": "", "So_don": "Số đơn"}, color="Trang_thai",
                 color_discrete_sequence=COLORS)
    fig.update_layout(showlegend=False)
    show_chart(fig)

    # nhận xét tự động
    if not sales.empty:
        top_prod = sales.groupby("San_pham")["Doanh_thu"].sum().idxmax()
        top_ch = sales.groupby("Kenh_ban")["Doanh_thu"].sum().idxmax()
        top_period = trend.loc[trend["Doanh thu"].idxmax(), "Thời gian"]
        notes = [
            f"Sản phẩm mang lại doanh thu cao nhất: **{top_prod}**.",
            f"Kênh bán hiệu quả nhất: **{top_ch}**.",
            f"Thời điểm doanh thu cao nhất: **{top_period:%d/%m/%Y}** (theo {granularity.lower()}).",
        ]
        if cancel_rate >= 15:
            notes.append(f"Tỷ lệ hủy đơn **{cancel_rate:.1f}%** khá cao, nên kiểm tra quy trình xác nhận và giao hàng.")
        st.subheader("💡 Nhận xét nhanh")
        for n in notes:
            st.markdown("- " + n)

# ---------------- Tab Sản phẩm ----------------
with tab2:
    if sales.empty:
        st.info("Chưa có dữ liệu sản phẩm.")
    else:
        prod = (
            sales.groupby("San_pham")
            .agg(Doanh_thu=("Doanh_thu", "sum"), So_luong=("So_luong", "sum"), So_don=("Doanh_thu", "size"))
            .reset_index()
            .sort_values("Doanh_thu", ascending=False)
        )
        if len(prod) > 3:
            top_n = st.slider("Số sản phẩm hiển thị", 3, min(20, len(prod)), min(8, len(prod)))
        else:
            top_n = len(prod)
        top = prod.head(top_n).sort_values("Doanh_thu")
        fig = px.bar(top, x="Doanh_thu", y="San_pham", orientation="h", text=top["Doanh_thu"].map(short_money),
                     title=f"Top {top_n} sản phẩm theo doanh thu", labels={"Doanh_thu": "Doanh thu", "San_pham": ""})
        fig.update_traces(marker_color=COLORS[2])
        fig.update_xaxes(tickformat=",.0f")
        show_chart(fig)

        table = prod.copy()
        table["Tỷ trọng"] = (table["Doanh_thu"] / table["Doanh_thu"].sum() * 100).round(1).astype(str) + "%"
        table["Doanh_thu"] = table["Doanh_thu"].map(money)
        table.columns = ["Sản phẩm", "Doanh thu", "Số lượng bán", "Số đơn", "Tỷ trọng"]
        show_table(table)

# ---------------- Tab Khách hàng ----------------
with tab3:
    if sales.empty:
        st.info("Chưa có dữ liệu khách hàng.")
    else:
        cust = (
            sales.groupby("Khach_hang")
            .agg(Chi_tieu=("Doanh_thu", "sum"), So_don=("Doanh_thu", "size"), Lan_cuoi=("Ngay_dat", "max"))
            .reset_index()
            .sort_values("Chi_tieu", ascending=False)
        )
        a, b = st.columns(2)
        a.metric("Khách mua lặp lại (từ 2 đơn)", int((cust["So_don"] >= 2).sum()))
        b.metric("Chi tiêu TB mỗi khách", money(cust["Chi_tieu"].mean()))

        top_c = cust.head(10).sort_values("Chi_tieu")
        fig = px.bar(top_c, x="Chi_tieu", y="Khach_hang", orientation="h",
                     title="Top 10 khách hàng chi tiêu nhiều nhất", labels={"Chi_tieu": "Chi tiêu", "Khach_hang": ""})
        fig.update_traces(marker_color=COLORS[3])
        fig.update_xaxes(tickformat=",.0f")
        show_chart(fig)

        table = cust.copy()
        table["Chi_tieu"] = table["Chi_tieu"].map(money)
        table["Lan_cuoi"] = table["Lan_cuoi"].dt.strftime("%d/%m/%Y")
        table.columns = ["Khách hàng", "Tổng chi tiêu", "Số đơn", "Mua gần nhất"]
        show_table(table)

# ---------------- Tab Dữ liệu ----------------
with tab4:
    st.write(f"**{len(df):,}** đơn hàng sau khi lọc.".replace(",", "."))
    view = df.drop(columns=["Huy"]).sort_values("Ngay_dat", ascending=False).copy()
    export = view.copy()
    view["Ngay_dat"] = view["Ngay_dat"].dt.strftime("%d/%m/%Y")
    show_table(view)
    st.download_button(
        "⬇️ Tải dữ liệu đã lọc (CSV)",
        export.to_csv(index=False).encode("utf-8-sig"),
        file_name="don_hang_da_loc.csv",
        mime="text/csv",
    )
