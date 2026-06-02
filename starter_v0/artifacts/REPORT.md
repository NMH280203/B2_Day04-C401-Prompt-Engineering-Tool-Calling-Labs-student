# Day 04 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: 105
- Members:
  - Nguyễn Mạnh Hiếu - 2A202600887
  - Mai Đức Vinh - 2A202600587
  - Nguyễn Đăng Khương - 2A202600584
- Provider/model: openrouter / openai/gpt-4o-mini

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent: tìm tin theo từ khóa / theo tài khoản, đọc URL, tổng hợp thành digest, loại bỏ trùng lặp, và gửi lên Telegram khi được xác nhận.

Ví dụ ngắn (1 dòng): Từ câu hỏi người dùng, agent chọn tool phù hợp (timeline/social_search/lookup/fetch), thu thập nội dung, format thành digest và chờ xác nhận trước khi gửi.

**Link dùng thử (deploy):**

> Dán link public để team khác mở thử ngay. Cách deploy nhanh bằng Cloudflare Tunnel xem README. Nếu deploy Vercel/Streamlit Cloud thì dán link đó.
>
> URL: (chưa deploy — placeholder)

## A2. Tool agent có

Liệt kê các tool agent đang dùng (gồm tool mới nhóm tự thêm). Mỗi tool 1 dòng: tên + làm được gì.

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | Hỏi lại người dùng khi thiếu thông tin (handle/URL/confirm) | không |
| timeline | Lấy bài đăng của một account (screenname) | không |
| social_search | Tìm tweet/thảo luận theo chủ đề hoặc top posts | không |
| lookup | Tìm web/news theo topic và timeframe | không |
| fetch | Đọc nội dung từ một URL đã cho | không |
| format | Định dạng/summarize danh sách item thành digest | không |
| dedupe | Loại bỏ URL/trùng lặp trong danh sách (tool nhóm thêm) | có |
| send | Gửi bài/tin lên Telegram (chỉ khi user confirm) | không |

## A3. Câu hỏi mẫu để thử

> 3–5 câu hỏi/yêu cầu mẫu để team khác tự thử agent ngay.

1. "Cho tôi 5 tweet mới nhất của Sam Altman." (expect: clarify nếu thiếu handle, hoặc timeline call với screenname `sama`)
2. "Tin AI hôm nay" (expect: lookup topic=news, timeframe=day và trả về sources)
3. "Đọc bài báo này và tóm tắt ngắn: <URL>" (expect: fetch -> format)
4. "So sánh tweet về 'Gemini' và các bài báo web ngày hôm nay" (expect: lookup + social_search, nếu user yêu cầu cả hai)
5. "Gửi tóm tắt này lên Telegram" (expect: clarify yes_no trước, rồi send only after confirmed)

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | Đo prompt starter xấu | — | 0.70 | runs/v0_B_base_openrouter_20260602T123152565649.json |
| v1 | system_prompt.md | Clarify/no_tool/send boundary | 0.70 | 0.70 | runs/v1_B_base_openrouter_20260602T123336025846.json |
| v2 | tools.yaml | Mô tả tool chi tiết → routing/args | 0.70 | 1.00 | runs/v2_B_base_openrouter_20260602T123628881196.json |
| v3 | prompt + tools + dedupe | Tool mới + giữ metric | 1.00 | 1.00 | runs/v3_B_base_openrouter_20260602T123846242430.json |

> Best base run file: `runs/v3_B_base_openrouter_20260602T123846242430.json`

## B2. Failure Analysis

Use actual failures from `results[*].result.failures`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R08, R14 | out_of_scope | send | Gọi send cho bài toán/coding | Prompt: refuse, no tools |
| R10, R11 | missing_info | timeline/fetch (guessed) | Thiếu handle/URL dẫn đến sai tool | Prompt + tools: clarify |
| R12 | wrong_boundary | send | Không hỏi yes_no trước khi send | tools.yaml + system_prompt: require clarify yes_no |
| R13 | wrong_tool | lookup (thiếu topic news) | Đoán sai tool khi user cần social_search | Rule: chỉ call both khi user explicit cả web và tweets |

## B3. Team Eval Cases

List the 10 cases added to `data/eval_group.json` (5 single turn + 5 multi turn).

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01 | timeline vs search | timeline satyanadella | PASS |
| G02 | chủ đề trên X | social_search | PASS |
| G03 | timeframe month | lookup news month | PASS |
| G04 | thiếu URL | clarify text | PASS |
| G05 | dịch thuật OOS | no_tool | PASS |
| G06 | multi clarify→timeline | timeline BillGates limit 5 | PASS |
| G07 | multi sửa limit | timeline sama limit 2 | PASS |
| G08 | bỏ X → web | lookup Gemini news day | PASS |
| G09 | Telegram boundary | clarify yes_no | PASS |
| G10 | tool dedupe | dedupe by url | PASS |

##  B4. Live Chat Evidence

Use `transcripts/*.transcript.json`.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | "Tin tức AI hôm nay có gì?" | lookup(query="AI", topic="news", timeframe="day") | v0+pbaff2db77928 | Trả về 5 bài báo AI mới nhất |
| 2 | "Tweet mới nhất của Sam Altman?" | timeline(screenname="sama", limit=5) | v0+pbaff2db77928 | 5 tweet gần nhất của @sama |
| 3 | "Tìm paper về Retrieval-Augmented Generation" | papers(query="Retrieval-Augmented Generation") | v0+pbaff2db77928 | Danh sách bài báo arXiv về RAG |
| 4 | "Gửi email cho bob@company.com" → cung cấp thêm subject+body → "Gửi đi" | clarify(yes_no) → send_email(confirmed=true) | v0+pbaff2db77928 | Email gửi thành công sau xác nhận |
| 5 | "Viết code Python tính Fibonacci" | (no tool) | v0+pbaff2db77928 | Từ chối lịch sự — ngoài phạm vi agent |

link: https://touch-from-commit-regularly.trycloudflare.com

## B5. Bonus Evidence

Only fill if your team did bonus.

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) | (not fully enabled) | clarify yes_no implemented; send guarded | Need explicit send confirmation; Telegram not fully tested |
| arXiv/company policy | (n/a) | (n/a) | (n/a) |
| UI (Streamlit) | `ui/app.py`, `ui/README.md` | Chat + tool trace expanders + demo buttons + transcript JSON | Chạy local; cần `.env`; RapidAPI 403 may affect timeline |

## B6. Reflection

- Which fixes belonged in `system_prompt.md`?
  - Clarify rules for not guessing handles/URLs; require yes_no before send; enforce single JSON output format.
- Which fixes belonged in `tools.yaml`?
  - Tool descriptions, when-to-use guidance, argument schemas (e.g., clarify yes_no, timeline screenname mapping), dedupe behavior.
- Which failure needed manual review instead of automatic grading?
  - Cases where tool arguments or external API errors (RapidAPI 403) caused inconsistent outputs; manual review needed for real-world URLs and API failures.
- What would you improve next?
  - Enable and test Telegram send in a sandbox, fix RapidAPI access for timeline, add automated JSON-response validator for model outputs, and add a small poster at `artifacts/poster.html` for demo.
