# Day 04 Lab v2 Report — Research Agent

## Team

- Team:105
- Members: Mai Đức Vinh 2A202600587
- Provider/model: OpenRouter / openai/gpt-4o-mini

## Final Metrics

- Final version: v3
- Final artifact_version: v3+pbaff2db77928+tfdd91191b1ac
- Best base run file: v3_B_base_openrouter_20260602T152559047934.json
- Base case accuracy: 1.0 (20/20)
- Base tool routing accuracy: 1.0
- Base argument accuracy: 1.0
- Group eval run file: v3_B_group_openrouter_20260602T144529955783.json
- Group eval accuracy: 1.0 (5/5)
- Chat transcript file: v0_openrouter_20260602T160120309018.transcript.json

## Version Evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline (system_prompt.md + tools.yaml) | Prompt gốc chưa có routing rõ ràng | 0.65 | 0.65 | v0_B_base_openrouter_20260602T123229763659.json |
| v1 | system_prompt.md — thêm routing rules cho lookup (query không chứa "tin tức", timeframe mapping) | Fix query arg và timeframe | 0.65 | 0.95 | v1_B_base_openrouter_20260602T125509718250.json |
| v2 | system_prompt.md — thêm boundary rules: out_of_scope từ chối, clarify trước khi gọi send/fetch khi thiếu info | Fix R08/R12/R14 out-of-scope và missing handle/URL | 0.95 | 1.0 | v2_B_base_openrouter_20260602T125727183316.json |
| v3 | system_prompt.md + tools.yaml — thêm send_email flow, email validation, no extra CC clarify rule | Thêm send_email tool + group eval 5 cases → 100% | 1.0 | 1.0 | v3_B_base_openrouter_20260602T152559047934.json |

## Failure Analysis

Use actual failures from `results[*].result.failures`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R03_web_news_routing | wrong_arg_value | lookup | query="AI news" thay vì "AI" — chứa từ "news" trong query | Thêm rule: query chỉ chứa từ khóa cốt lõi, không chứa "tin tức"/"news" |
| R08_out_of_scope | out_of_scope | send | Gọi `send` cho yêu cầu coding/off-topic | Thêm rule: từ chối lịch sự, không gọi tool nào khi ngoài phạm vi |
| R10_missing_handle | missing_info | timeline | Gọi `timeline` khi không có tên người — tự đoán | Thêm rule: thiếu handle → `clarify(text)` hỏi tên, KHÔNG tự gọi timeline |
| R11_missing_url | missing_info | fetch | Gọi `fetch` khi chưa có URL cụ thể | Thêm rule: thiếu URL → `clarify(text)` hỏi link |
| R12_confirm_before_send | wrong_boundary | send | Gọi `send` trực tiếp không qua xác nhận | Thêm rule: LUÔN `clarify(yes_no)` trước khi gọi `send` |
| R13_parallel_web_tweets | wrong_arg_value | lookup + social_search | lookup query="AI news", topic=None — thiếu topic=news và timeframe | Fix routing rules cho parallel call với đúng args |
| R14_out_of_scope_coding | out_of_scope | send | Gọi `send` cho yêu cầu viết code Python | Cùng fix với R08 — out_of_scope rule |

## Team Eval Cases

List at least 5 cases added to `data/eval_group.json`.

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_email_missing_recipient | "Gửi email cho team" thiếu địa chỉ → phải hỏi lại | clarify(response_type=text) | PASS ✅ |
| G02_email_confirm_before_send | Có đủ to/subject/body + "Không cần CC" → xác nhận trước khi gửi | clarify(response_type=yes_no) duy nhất, không hỏi CC | PASS ✅ |
| G03_papers_search_routing | Tìm research papers về RAG → dùng papers, không phải lookup | papers(query=...) | PASS ✅ |
| G04_policy_routing | Hỏi chính sách trích dẫn nguồn nội bộ → dùng policy | policy(policy_area=source_citation) | PASS ✅ |
| G05_multiturn_email_full_info_confirm | 3 turns: cung cấp to → subject+body → "Gửi đi" → vẫn phải xác nhận | clarify(response_type=yes_no) không tự gọi send_email | PASS ✅ |

## Live Chat Evidence

Use `transcripts/*.transcript.json`.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | "Tin tức AI hôm nay có gì?" | lookup(query="AI", topic="news", timeframe="day") | v0+pbaff2db77928 | Trả về 5 bài báo AI mới nhất |
| 2 | "Tweet mới nhất của Sam Altman?" | timeline(screenname="sama", limit=5) | v0+pbaff2db77928 | 5 tweet gần nhất của @sama |
| 3 | "Tìm paper về Retrieval-Augmented Generation" | papers(query="Retrieval-Augmented Generation") | v0+pbaff2db77928 | Danh sách bài báo arXiv về RAG |
| 4 | "Gửi email cho bob@company.com" → cung cấp thêm subject+body → "Gửi đi" | clarify(yes_no) → send_email(confirmed=true) | v0+pbaff2db77928 | Email gửi thành công sau xác nhận |
| 5 | "Viết code Python tính Fibonacci" | (no tool) | v0+pbaff2db77928 | Từ chối lịch sự — ngoài phạm vi agent |

## Bonus Evidence

Only fill if your team did bonus.

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) | — | Không sử dụng Telegram | — |
| arXiv/company policy | v0_openrouter_20260602T160120309018.transcript.json | papers + paper_text đọc bài arXiv; policy tra cứu source_citation | Agent dùng đúng tool cho từng loại — không nhầm lookup |
| UI | ui/index.html | Web UI với Tool Inspector hiển thị type dữ liệu input/output của mỗi tool call | — |
| send_email | tools/send_email/tool.py | Gửi email qua Gmail SMTP với SMTP_SSL port 465; validate format email trước khi gửi | Luôn clarify(yes_no) trước khi gửi; không hỏi CC khi không cần; báo lỗi và yêu cầu nhập lại nếu email sai |

## Reflection

- **Which fixes belonged in `system_prompt.md`?**
  - Routing rules (lookup vs fetch vs papers vs policy), name→handle mapping, timeframe keyword mapping, out_of_scope từ chối, boundary rules (clarify trước send/send_email), email error recovery flow khi invalid_email.
  - → Tất cả logic quyết định "khi nào dùng tool nào" và "phải làm gì khi tool trả lỗi" đều thuộc system_prompt.

- **Which fixes belonged in `tools.yaml`?**
  - Mô tả tham số chi tiết (required vs optional, enum values), cảnh báo boundary trong description tool (CRITICAL, IMPORTANT), rule "chỉ 1 clarify khi xác nhận email — không hỏi CC".
  - → Thông tin giúp model điền đúng args và hiểu giới hạn của từng tool.

- **Which failure needed manual review instead of automatic grading?**
  - R08/R14 (out_of_scope): model gọi `send` với nội dung "xin lỗi tôi không hỗ trợ" — về mặt nội dung đúng nhưng grader đánh là sai vì gọi tool. Cần reviewer đọc nội dung gửi để phán xét.
  - G02 (email confirm): model hỏi thêm về CC — hành vi hợp lý nhưng sai theo spec "1 clarify duy nhất". Boundary này mơ hồ, cần con người quyết định.

- **What would you improve next?**
  - Thêm streaming response để UI hiển thị real-time (không phải chờ tool xong mới thấy).
  - Thêm memory/context window thông minh hơn để không bị mất thông tin trong multi-turn dài.
  - Thêm tool `schedule_send` để lên lịch gửi email/bản tin tự động.
  - Cải thiện test case phong phú hơn, đặc biệt multi-turn phức tạp và parallel tool calls.
  - Deploy lên cloud (Railway hoặc Fly.io) để có link cố định thay vì tunnel tạm thời.
