import streamlit as st
import pandas as pd
import subprocess
import json
import gspread
from google.oauth2.service_account import Credentials
import os
import sys

st.title("FMarket Data Scraper")

SHEET_URL = "https://docs.google.com/spreadsheets/d/19H1Tvyy1Of36PIqonFM2OQGYBFjhDHHSxGWPMlb1RBc/edit?usp=sharing"

# Cài đặt Playwright khi lần đầu chạy trên Streamlit Cloud
@st.cache_resource
def install_playwright():
    """Cài đặt Playwright browsers một lần duy nhất"""
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"],
                      check=True, capture_output=True)
        return True
    except Exception as e:
        st.error(f"Không thể cài Playwright: {e}")
        return False

# Cài đặt Playwright
install_playwright()

def get_data():
    # Lấy credentials từ Streamlit secrets
    email = st.secrets["fmarket"]["email"]
    password = st.secrets["fmarket"]["password"]

    script = f"""
from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto("https://fmarket.vn/trade/auth/login")
    page.locator("#focusEmail").fill("{email}")
    page.locator("#focusPassword").fill("{password}")
    page.locator("#focusPassword").press("Enter")

    page.wait_for_load_state("networkidle")
    page.locator("#table-products div").filter(has_text="Tất cả Quỹ trái phiếu").nth(2).click()
    page.wait_for_timeout(2000)

    data = page.evaluate(\"\"\"() => {{
        const rows = Array.from(document.querySelectorAll('#table-products table tbody tr'));
        return rows.map(row => {{
            const cells = Array.from(row.querySelectorAll('td'));
            return cells.map(cell => cell.innerText.trim());
        }});
    }}\"\"\")

    browser.close()
    print(json.dumps(data))
"""

    result = subprocess.run([sys.executable, '-c', script], capture_output=True, text=True)

    # Debug: Hiển thị output và error
    if result.returncode != 0:
        st.error(f"Subprocess failed with return code {result.returncode}")
        st.error(f"STDERR: {result.stderr}")
        st.info(f"STDOUT: {result.stdout}")
        raise Exception(f"Playwright script failed: {result.stderr}")

    if not result.stdout.strip():
        st.error("Subprocess returned empty output")
        st.error(f"STDERR: {result.stderr}")
        raise Exception("No data returned from Playwright")

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse JSON: {e}")
        st.error(f"Raw output: {result.stdout[:500]}")
        raise

if st.button("Get Data"):
    with st.spinner("Đang login..."):
        data = get_data()

        st.success("Done!")

        if data:
            df = pd.DataFrame(data)

            # Xử lý cột 0: lấy phần trước "Quỹ"
            df[0] = df[0].str.split('Quỹ').str[0].str.strip()

            # Xử lý cột 2: tách NAV và ngày
            df['NAV'] = df[2].str.split('Theo').str[0].str.strip()
            df['Ngày báo cáo'] = df[2].str.split('tại').str[1].str.strip()

            # Convert NAV sang số: loại bỏ dấu phẩy và convert sang float
            df['NAV'] = df['NAV'].str.replace(',', '').astype(float)

            # Convert ngày sang datetime với năm hiện tại
            from datetime import datetime
            current_year = datetime.now().year
            current_month = datetime.now().month

            df['Ngày báo cáo'] = df['Ngày báo cáo'].apply(lambda x: f"{x}/{current_year}" if pd.notna(x) else x)
            df['Ngày báo cáo'] = pd.to_datetime(df['Ngày báo cáo'], format='%d/%m/%Y', errors='coerce')

            # Nếu tháng báo cáo = 12 và tháng hiện tại = 1, trừ 1 năm
            def adjust_year(date):
                if pd.notna(date) and date.month == 12 and current_month == 1:
                    return date.replace(year=date.year - 1)
                return date

            df['Ngày báo cáo'] = df['Ngày báo cáo'].apply(adjust_year)

            # Thêm cột Ngày NAV = Ngày báo cáo - 1
            df['Ngày NAV'] = df['Ngày báo cáo'] - pd.Timedelta(days=1)

            df['Ngày báo cáo'] = df['Ngày báo cáo'].dt.strftime('%d/%m/%Y')
            df['Ngày NAV'] = df['Ngày NAV'].dt.strftime('%d/%m/%Y')

            # Xóa cột 2 cũ
            df = df.drop(columns=[2])

            # Chuẩn bị data để lưu vào Google Sheets
            df_export = pd.DataFrame({
                'Date report': df['Ngày báo cáo'],
                'Date NAV': df['Ngày NAV'],
                'Fund': df[0],
                'NAV': df['NAV']
            })

            st.dataframe(df)

            # Lưu vào Google Sheets
            try:
                # Lấy credentials từ secrets
                credentials = Credentials.from_service_account_info(
                    st.secrets["gcp_service_account"],
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
                client = gspread.authorize(credentials)

                # Mở sheet
                sheet = client.open_by_url(SHEET_URL).sheet1

                # Đọc toàn bộ dữ liệu hiện có (bỏ qua header)
                existing_data = sheet.get_all_values()

                # Nếu có header, bỏ dòng đầu
                if len(existing_data) > 0:
                    header = existing_data[0]
                    existing_rows = existing_data[1:]
                else:
                    existing_rows = []
                    # Thêm header nếu sheet trống
                    sheet.append_row(['Date report', 'Date NAV', 'Fund', 'NAV'])

                # Tạo dict để tracking: key = (Fund, Date NAV), value = row index
                existing_dict = {}
                for idx, row in enumerate(existing_rows):
                    if len(row) >= 4:
                        # row[2] = Fund, row[1] = Date NAV
                        key = (row[2], row[1])
                        existing_dict[key] = idx + 2  # +2 vì: +1 cho header, +1 vì gspread index từ 1

                updated_count = 0
                appended_count = 0

                # Xử lý từng row mới
                for _, row in df_export.iterrows():
                    date_report = row['Date report']
                    date_nav = row['Date NAV']
                    fund = row['Fund']
                    nav = row['NAV']

                    key = (fund, date_nav)

                    if key in existing_dict:
                        # Update: tìm row index và update
                        row_index = existing_dict[key]
                        sheet.update(f'A{row_index}:D{row_index}', [[date_report, date_nav, fund, nav]])
                        updated_count += 1
                    else:
                        # Append: thêm dòng mới
                        sheet.append_row([date_report, date_nav, fund, nav])
                        appended_count += 1

                st.success(f"✅ Đã lưu vào Google Sheets! (Updated: {updated_count}, Appended: {appended_count})")
            except Exception as e:
                st.error(f"Lỗi khi lưu: {e}")

            csv = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button("Download CSV", csv, "data.csv", "text/csv")
        else:
            st.warning("Không có data")
