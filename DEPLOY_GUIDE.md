# Hướng Dẫn Deploy FMarket Scraper Lên Streamlit Cloud

## ⚠️ Vấn Đề Đã Gặp

**Lỗi:** `json.decoder.JSONDecodeError` khi dùng subprocess

**Nguyên nhân:**
- Subprocess approach không ổn định trên Streamlit Cloud
- Playwright có thể fail silently trong subprocess
- Output bị trộn với error messages

## ✅ Giải Pháp

Sử dụng **app_v2.py** thay vì app.py vì:
- ✅ Chạy Playwright trực tiếp (không qua subprocess)
- ✅ Error handling tốt hơn
- ✅ Dễ debug hơn trên cloud
- ✅ Ổn định hơn

## 📋 Các File Cần Push Lên GitHub

```bash
git add app_v2.py          # Main app (recommended)
git add requirements.txt    # Python dependencies
git add packages.txt        # System dependencies
git add .gitignore         # Bảo vệ credentials
git add CLAUDE.md          # Documentation
git add .streamlit/secrets.toml.example  # Template
```

**KHÔNG push:**
- `.env`
- `.streamlit/secrets.toml`
- `.claude/`

## 🚀 Các Bước Deploy

### 1. Chuẩn Bị Git Repository

```bash
cd "d:\OneDrive - DRAGON CAPITAL\Claude\FMarket"

# Init git
git init

# Add files an toàn
git add app_v2.py
git add requirements.txt
git add packages.txt
git add .gitignore
git add CLAUDE.md
git add .streamlit/secrets.toml.example
git add DEPLOY_GUIDE.md

# Commit
git commit -m "Deploy FMarket scraper to Streamlit Cloud"

# Add remote (thay your-username và repo-name)
git remote add origin https://github.com/your-username/fmarket-scraper.git

# Push
git push -u origin main
```

### 2. Deploy Trên Streamlit Cloud

1. Truy cập: https://share.streamlit.io/
2. Sign in với GitHub
3. Click **New app**
4. Chọn repository: `fmarket-scraper`
5. **Main file path:** `app_v2.py` ⚠️ (QUAN TRỌNG!)
6. Click **Advanced settings**
7. **Python version:** 3.11 (hoặc 3.10)
8. Click **Deploy**

### 3. Cấu Hình Secrets

Sau khi deploy, vào **App settings** → **Secrets** và paste:

```toml
[fmarket]
email = "dangvu@dragoncapital.com"
password = "your-password-here"

[gcp_service_account]
type = "service_account"
project_id = "dangvu-n8n"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "dc-324@dangvu-n8n.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
```

Copy từ file `.streamlit/secrets.toml` local của bạn.

## 🔧 Troubleshooting

### Nếu vẫn gặp lỗi Playwright:

**1. Kiểm tra logs:**
- Click vào "Manage app" trên dashboard
- Xem logs chi tiết
- Tìm error message cụ thể

**2. Thử thêm vào requirements.txt:**
```
playwright==1.40.0
```

**3. Kiểm tra packages.txt có đầy đủ:**
```
chromium
chromium-driver
libnss3
libnspr4
libatk1.0-0
libatk-bridge2.0-0
libcups2
libdrm2
libxkbcommon0
libxcomposite1
libxdamage1
libxfixes3
libxrandr2
libgbm1
libasound2
```

**4. Force reinstall:**
- Vào App settings → Reboot app
- Xóa cache: Settings → Clear cache → Reboot

### Nếu login FMarket fail:

- Kiểm tra credentials trong Secrets
- Test thử trên local trước
- Check xem FMarket có thay đổi UI không

## 📊 So Sánh app.py vs app_v2.py

| Feature | app.py (subprocess) | app_v2.py (direct) |
|---------|-------------------|-------------------|
| Approach | Subprocess | Direct import |
| Stability | ❌ Unstable trên cloud | ✅ Stable |
| Error handling | ⚠️ Khó debug | ✅ Dễ debug |
| Performance | Slower (spawn process) | Faster |
| Recommended | ❌ NO | ✅ YES |

## 🎯 Best Practices

1. **Luôn dùng app_v2.py** khi deploy
2. **Test local trước** bằng: `streamlit run app_v2.py`
3. **Monitor logs** sau khi deploy lần đầu
4. **Rotate credentials** nếu từng bị leak trong git

## 📝 Notes

- First deploy có thể mất 5-10 phút để cài Playwright
- Cold start sau đó ~30 giây
- Free tier: 1GB RAM, có thể sleep nếu không dùng
