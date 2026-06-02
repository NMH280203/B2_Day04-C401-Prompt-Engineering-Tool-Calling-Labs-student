# send_email tool

Gửi email qua SMTP (mặc định Gmail).

## Cấu hình (.env)

```
EMAIL_SENDER=your_address@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_SMTP_HOST=smtp.gmail.com   # optional, default
EMAIL_SMTP_PORT=465              # optional, default (SSL)
```

## Gmail App Password

1. Bật 2-Step Verification: https://myaccount.google.com/security
2. Tạo App Password: https://myaccount.google.com/apppasswords
3. Chọn "Mail" → "Windows Computer" → Copy mật khẩu 16 ký tự vào EMAIL_PASSWORD
