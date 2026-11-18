# Hướng dẫn triển khai: Streamlit Cloud (xử lý) + Vercel (trang chính)

Vercel không chạy được ứng dụng Streamlit vì Streamlit cần máy chủ chạy liên tục và bộ thư viện phân tích vượt giới hạn 250 MB.
Vì vậy: ứng dụng chạy trên Streamlit Cloud (miễn phí), Vercel phục vụ trang chính `web/index.html` và nhúng ứng dụng vào.

## Bước 1 — Đưa toàn bộ thư mục này lên GitHub
Tạo repo Public, tải lên TẤT CẢ tệp và thư mục trong gói này (kiểm tra có `.streamlit/config.toml`).

## Bước 2 — Chạy ứng dụng trên Streamlit Cloud
1. share.streamlit.io → Create app → Deploy a public app from GitHub.
2. Repository: repo vừa tạo · Branch: main · Main file path: `app.py`.
3. Advanced settings → Python 3.11 → Secrets:
   GEMINI_API_KEY = "AIza..."
   GEMINI_MODEL = "gemini-2.5-flash"
4. Deploy, chờ 3–5 phút, copy link dạng https://ten-app.streamlit.app

## Bước 3 — Gắn link vào trang Vercel
Trên GitHub mở `web/index.html` → bấm bút chì → thay
`https://TEN-APP-CUA-BAN.streamlit.app` bằng link ở Bước 2 → Commit.

## Bước 4 — Triển khai trên Vercel
1. vercel.com → Add New → Project → Import repo vừa tạo.
2. Framework Preset: Other. Không cần sửa gì khác (tệp `vercel.json` đã cấu hình sẵn).
3. Deploy → nhận link dạng https://ten-du-an.vercel.app

## Chạy trên máy cá nhân
pip install -r requirements.txt
streamlit run app.py
