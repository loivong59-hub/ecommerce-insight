import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import date

st.set_page_config(
    page_title="Ecom Insight - Phân tích bán hàng",
    page_icon="📊",
    layout="wide"
)

# ---------- GIAO DIỆN ----------
st.markdown("""
<style>
    .main {background-color: #f6f8fc;}
    [data-testid="stMetric"] {
        background: white;
        border: 1px solid #e8edf5;
        padding: 16px 18px;
        border-radius: 14px;
        box-shadow: 0 2px 8px rgba(20,40,80,.04);
    }
    .block-container {padding-top: 1.8rem; padding-bottom: 2rem;}
    h1, h2, h3 {color: #17365d;}
    div[data-testid="stSidebar"] {background: #eef3fb;}
</style>
""", unsafe_allow_html=True)

# ---------- DỮ LIỆU MẪU ----------
@st.cache_data
def make_sample_data():
    rng = np.random.default_rng(17)
    products = ["Tai nghe Bluetooth", "Áo thun", "Bình giữ nhiệt", "Chuột không dây",
                "Giày thể thao", "Balo laptop", "Ốp điện thoại", "Đèn bàn"]
    categories = {
        "Tai nghe Bluetooth": "Điện tử", "Áo thun": "Thời trang",
        "Bình giữ nhiệt": "Gia dụng", "Chuột không dây": "Điện tử",
        "Giày thể thao": "Thời trang", "Balo laptop": "Phụ kiện",
        "Ốp điện thoại": "Phụ kiện", "Đèn bàn": "Gia dụng"
    }
    prices = {
        "Tai nghe Bluetooth": 450000, "Áo thun": 180000,
        "Bình giữ nhiệt": 220000, "Chuột không dây": 250000,
        "Giày thể thao": 650000, "Balo laptop": 390000,
        "Ốp điện thoại": 90000, "Đèn bàn": 280000
    }
    names = ["Nguyễn Minh Anh", "Trần Gia Huy", "Lê Hoàng Yến", "Phạm Tuấn Kiệt",
             "Võ Ngọc Hà", "Đặng Quốc Bảo", "Bùi Thanh Tâm", "Huỳnh Đức Long",
             "Đỗ Khánh Linh", "Phan Nhật Nam", "Mai Phương Thảo", "Ngô Anh Tú"]
    channels = ["Shopee", "TikTok Shop", "Website", "Facebook"]
    statuses = ["Hoàn thành", "Hoàn thành", "Hoàn thành", "Đang giao", "Đã hủy"]
    rows = []
    start = pd.Timestamp.today().normalize() - pd.Timedelta(days=179)
    for i in range(450):
        product = rng.choice(products)
        qty = int(rng.choice([1, 1, 1, 2, 2, 3]))
        unit = prices[product]
        discount = int(rng.choice([0, 0, 0, 10000, 20000, 30000]))
        rows.append({
            "Ma_don_hang": f"DH{i+1:04d}",
            "Ngay_dat": start + pd.Timedelta(days=int(rng.integers(0, 180))),
            "Khach_hang": rng.choice(names),
            "San_pham": product,
            "Danh_muc": categories[product],
            "So_luong": qty,
            "Don_gia": unit,
            "Giam_gia": discount,
            "Kenh_ban": rng.choice(channels, p=[0.40, 0.30, 0.15, 0.15]),
            "Trang_thai": rng.choice(statuses, p=[0.72, 0.12, 0.16])
        })
    df = pd.DataFrame(rows)
    df["Doanh_thu"] = df["So_luong"] * df["Don_gia"] - df["Giam_gia"]
    return df

def normalize_data(df):
    required = ["Ngay_dat", "Khach_hang", "San_pham", "So_luong", "Don_gia"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        st.error("File thiếu cột bắt buộc: " + ", ".join(missing))
        st.info("Các cột cần có: Ngay_dat, Khach_hang, San_pham, So_luong, Don_gia. Có thể xem file dữ liệu mẫu đi kèm.")
        st.stop()
    df = df.copy()
    df["Ngay_dat"] = pd.to_datetime(df["Ngay_dat"], errors="coerce")
    df["So_luong"] = pd.to_numeric(df["So_luong"], errors="coerce").fillna(0)
    df["Don_gia"] = pd.to_numeric(df["Don_gia"], errors="coerce").fillna(0)
    if "Giam_gia" not in df.columns:
        df["Giam_gia"] = 0
    df["Giam_gia"] = pd.to_numeric(df["Giam_gia"], errors="coerce").fillna(0)
    if "Danh_muc" not in df.columns:
        df["Danh_muc"] = "Chưa phân loại"
    if "Kenh_ban" not in df.columns:
        df["Kenh_ban"] = "Không xác định"
    if "Trang_thai" not in df.columns:
        df["Trang_thai"] = "Hoàn thành"
    df = df.dropna(subset=["Ngay_dat", "Khach_hang", "San_pham"])
