# Research Agent — Streamlit UI

Giao diện web local để chat và demo tool-calling (thay cho `python chat.py`).

## Chạy app

```bash
cd starter_v0
source .venv/bin/activate
pip install -r requirements.txt
streamlit run ui/app.py
```

Mở URL Streamlit in ra (thường http://localhost:8501).

## Yêu cầu

- File `.env` trong `starter_v0/` (copy từ `.env.example`) với ít nhất `OPENROUTER_API_KEY`.
- Các key research: `TAVILY_API_KEY`, `FIRECRAWL_API_KEY`, `RAPIDAPI_KEY` (Twitter có thể 403 — UI vẫn hiển thị tool trace).

## Demo nhanh (sidebar)

1. **Tin AI hôm nay** — kỳ vọng `lookup` (topic news, timeframe day).
2. **Tweet thiếu handle** — kỳ vọng `clarify` (không đoán account).
3. **Đăng Telegram** — kỳ vọng `clarify` với `response_type` yes/no, không `send` ngay.

## Transcript

Mỗi lượt chat ghi vào `transcripts/*.transcript.json` (cùng schema CLI), field `source: streamlit_ui`.

## Lưu ý

- Refresh trang trình duyệt sẽ reset session chat (bình thường với Streamlit).
- Không commit `.env` hoặc API keys.
