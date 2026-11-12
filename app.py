import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Ecom Insight", page_icon="📊", layout="wide")

st.markdown("""
<style>
.main {background:#f6f8fc;}
[data-testid="stMetric"] {
    background:white; padding:16px; border-radius:12px;
    border:1px solid #e7edf5;
}
.block-container {padding-top:1.5rem;}
</style>
""", unsafe_allow_html=True)

def money(x):
    return f"{x:,.0f} đ".replace(",", ".")

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
        "Nguyễn Minh Anh", "Trần Gia Huy", "Lê Hoàng Yến",
        "Phạm Tuấn Kiệt", "Võ Ngọc Hà", "Đặng Quốc Bảo",
        "Bùi Thanh Tâm", "Huỳnh Đức Long", "Đỗ Khánh Linh",
        "Phan Nhật Nam", "Mai Phương Thảo", "Ngô Anh Tú"
    ]
    channels = ["Shopee", "TikTok Shop", "Website", "Facebook"]
    statuses = ["Hoàn thành", "Đang giao", "Đã hủy"]
    start = pd.Timestamp.today().normalize() - pd.Timedelta(days=179)
    rows = []
    product_names = list(products.keys())
    for i in range(300):
        product = rng.choice(product_names)
        category, price = products[product]
        qty = int(rng.choice([1, 1, 1, 2, 2, 3]))
        discount = int(rng.choice([0, 0, 0, 10000, 20000, 30000]))
        rows.append({
            "Ma_don_hang": f"DH{i+1:04d}",
            "Ngay_dat": start + pd.Timedelta(days=int(rng.integers(0, 180))),
            "Khach_hang": rng.choice(customers),
            "San_pham": product,
            "Danh_muc": category,
            "So_luong": qty,
            "Don_gia": price,
            "Giam_gia": discount,
            "Kenh_ban": rng.choice(channels, p=[.4, .3, .15, .15]),
            "Trang_thai": rng.choice(statuses, p=[.72, .12, .16])
        })
    df = pd.DataFrame(rows)
    df["Doanh_thu"] = (df["So_luong"] * df["Don_gia"] - df["Giam_gia"]).clip(lower=0)
    return df

def prepare_data(df):
    df = df.copy()
    required = ["Ngay_dat", "Khach_hang", "San_pham", "So_luong", "Don_gia"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        st.error("File CSV thiếu cột: " + ", ".join(missing))
        st.stop()

    df["Ngay_dat"] = pd.to_datetime(df["Ngay_dat"], errors="coerce")
    df["So_luong"] = pd.to_numeric(df["So_luong"], errors="coerce").fillna(0)
    df["Don_gia"] = pd.to_numeric(df["Don_gia"], errors="coerce").fillna(0)
    if "Giam_gia" not in df.columns:
        df["Giam_gia"] = 0
    df["Giam_gia"] = pd.to_numeric(df["Giam_gia"], errors="coerce").fillna(0)
    for col, default in [("Danh_muc", "Chưa phân loại"),
                         ("Kenh_ban", "Không xác định"),
                         ("Trang_thai", "Hoàn thành")]:
        if col not in df.columns:
            df[col] = default
    df = df.dropna(subset=["Ngay_dat", "Khach_hang", "San_pham"])
    df["Doanh_thu"] = (df["So_luong"] * df["Don_gia"] - df["Giam_gia"]).clip(lower=0)
    return df

# 1) Nạp dữ liệu trước
st.sidebar.title("📊 Ecom Insight")
st.sidebar.caption("Phân tích kinh doanh thương mại điện tử")
uploaded = st.sidebar.file_uploader("Tải dữ liệu đơn hàng CSV", type=["csv"])
if uploaded is not None:
    try:
        raw_data = pd.read_csv(uploaded)
        data = prepare_data(raw_data)
        st.sidebar.success("Đã tải dữ liệu của bạn.")
    except Exception as error:
        st.sidebar.error(f"Không đọc được CSV: {error}")
        st.stop()
else:
    data = sample_data()
    st.sidebar.info("Đang dùng 300 đơn hàng mẫu.")
