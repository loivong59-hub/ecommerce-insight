cancel_rate = cancelled / len(filtered) * 100 if len(filtered) else 0

m1, m2, m3, m4 = st.columns(4)
m1.metric("Tổng doanh thu", vnd(revenue))
m2.metric("Đơn hàng hoàn thành", f"{orders:,}".replace(",", "."))
m3.metric("Khách hàng", f"{customers:,}".replace(",", "."))
m4.metric("Giá trị đơn trung bình", vnd(aov))

m5, m6, m7 = st.columns(3)
m5.metric("Sản phẩm đã bán", f"{units:,.0f}".replace(",", "."))
m6.metric("Tỷ lệ đơn bị hủy", f"{cancel_rate:.1f}%")
m7.metric("Số đơn trong bộ lọc", f"{len(filtered):,}".replace(",", "."))

# ---------- CÁC TAB ----------
tab1, tab2, tab3, tab4 = st.tabs(["🏠 Tổng quan", "📦 Sản phẩm", "👥 Khách hàng", "📄 Dữ liệu đơn hàng"])

with tab1:
    left, right = st.columns([1.65, 1])
    with left:
        st.subheader("Doanh thu theo thời gian")
        trend = completed.copy()
        trend["Tháng"] = trend["Ngay_dat"].dt.to_period("M").astype(str)
        monthly = trend.groupby("Tháng", as_index=False)["Doanh_thu"].sum()
        fig = px.line(monthly, x="Tháng", y="Doanh_thu", markers=True,
                      labels={"Doanh_thu": "Doanh thu (VNĐ)", "Tháng": "Tháng"})
        fig.update_layout(margin=dict(l=10, r=10, t=20, b=10), height=340)
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.subheader("Doanh thu theo kênh")
        by_channel = completed.groupby("Kenh_ban", as_index=False)["Doanh_thu"].sum().sort_values("Doanh_thu", ascending=False)
        fig2 = px.pie(by_channel, names="Kenh_ban", values="Doanh_thu", hole=0.48)
        fig2.update_layout(margin=dict(l=5, r=5, t=20, b=5), height=340)
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Tình trạng đơn hàng")
    status = filtered.groupby("Trang_thai", as_index=False).size().rename(columns={"size": "Số đơn"})
    fig3 = px.bar(status, x="Trang_thai", y="Số đơn", text="Số đơn",
                  labels={"Trang_thai": "Trạng thái", "Số đơn": "Số lượng"})
    fig3.update_layout(showlegend=False, height=300, margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(fig3, use_container_width=True)

with tab2:
    st.subheader("Hiệu quả kinh doanh theo sản phẩm")
    product_perf = completed.groupby(["San_pham", "Danh_muc"], as_index=False).agg(
        Doanh_thu=("Doanh_thu", "sum"), So_luong_ban=("So_luong", "sum"),
        So_don=("San_pham", "count")
    ).sort_values("Doanh_thu", ascending=False)
    p1, p2 = st.columns(2)
    with p1:
        st.markdown("**Top sản phẩm theo doanh thu**")
        fig4 = px.bar(product_perf.head(8).sort_values("Doanh_thu"),
                      x="Doanh_thu", y="San_pham", orientation="h",
                      labels={"Doanh_thu": "Doanh thu (VNĐ)", "San_pham": "Sản phẩm"})
        fig4.update_layout(height=360, margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(fig4, use_container_width=True)
    with p2:
        st.markdown("**Số lượng bán theo danh mục**")
        cat_perf = completed.groupby("Danh_muc", as_index=False)["So_luong"].sum()
        fig5 = px.pie(cat_perf, names="Danh_muc", values="So_luong", hole=0.4)
        fig5.update_layout(height=360, margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(fig5, use_container_width=True)
    st.dataframe(product_perf.style.format({"Doanh_thu": "{:,.0f} đ", "So_luong_ban": "{:,.0f}", "So_don": "{:,.0f}"}),
                 use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Phân tích khách hàng")
    customer_perf = completed.groupby("Khach_hang", as_index=False).agg(
        Tong_chi_tieu=("Doanh_thu", "sum"),
        So_don=("Khach_hang", "count"),
        Tong_san_pham=("So_luong", "sum")
    ).sort_values("Tong_chi_tieu", ascending=False)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Top 10 khách hàng chi tiêu nhiều nhất**")
        fig6 = px.bar(customer_perf.head(10).sort_values("Tong_chi_tieu"),
                      x="Tong_chi_tieu", y="Khach_hang", orientation="h",
                      labels={"Tong_chi_tieu": "Tổng chi tiêu (VNĐ)", "Khach_hang": "Khách hàng"})
        fig6.update_layout(height=380, margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(fig6, use_container_width=True)
    with c2:
        st.markdown("**Tần suất mua hàng**")
        fig7 = px.histogram(customer_perf, x="So_don", nbins=10,
                            labels={"So_don": "Số đơn hàng", "count": "Số khách hàng"})
        fig7.update_layout(height=380, margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(fig7, use_container_width=True)
    st.dataframe(customer_perf.style.format({"Tong_chi_tieu": "{:,.0f} đ", "So_don": "{:,.0f}", "Tong_san_pham": "{:,.0f}"}),
                 use_container_width=True, hide_index=True)

with tab4:
    st.subheader("Chi tiết đơn hàng")
    search = st.text_input("🔎 Tìm theo mã đơn, tên khách hàng hoặc sản phẩm")
    display = filtered.copy()
    if search:
        mask = (
            display.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False)).any(axis=1)
        )
        display = display[mask]
    st.dataframe(display.sort_values("Ngay_dat", ascending=False), use_container_width=True, hide_index=True)
    csv = display.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ Tải dữ liệu đang xem (CSV)", data=csv,
                       file_name="du_lieu_don_hang_da_loc.csv", mime="text/csv")

# ---------- GỢI Ý KINH DOANH ----------
st.markdown("---")
st.subheader("💡 Gợi ý hỗ trợ ra quyết định")
best_product = product_perf.iloc[0]["San_pham"] if not product_perf.empty else "Chưa có dữ liệu"
best_channel = by_channel.iloc[0]["Kenh_ban"] if not by_channel.empty else "Chưa có dữ liệu"
top_customer = customer_perf.iloc[0]["Khach_hang"] if not customer_perf.empty else "Chưa có dữ liệu"
recommendations = [
    f"Sản phẩm tạo doanh thu cao nhất trong dữ liệu đang lọc là **{best_product}**. Cửa hàng có thể ưu tiên tồn kho và quảng bá sản phẩm này.",
    f"Kênh bán đóng góp doanh thu cao nhất là **{best_channel}**. Nên tiếp tục theo dõi hiệu quả quảng cáo và chi phí trên kênh này.",
    f"Khách hàng có tổng chi tiêu cao nhất là **{top_customer}**. Có thể triển khai chương trình khách hàng thân thiết, ưu đãi mua lại.",
    f"Tỷ lệ đơn hủy hiện tại là **{cancel_rate:.1f}%**. Nếu tỷ lệ cao, nên kiểm tra thời gian giao hàng, mô tả sản phẩm và quy trình xác nhận đơn."
]
for item in recommendations:
    st.markdown("- " + item)

st.caption("Lưu ý: Đây là công cụ hỗ trợ phân tích dựa trên dữ liệu đơn hàng. Dữ liệu mẫu chỉ phục vụ minh họa; kết quả thực tế phụ thuộc vào dữ liệu cửa hàng tải lên.")

