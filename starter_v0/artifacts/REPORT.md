# Day 04 Lab v2 Report — Research Agent

## Team

- Team: 105
- Members: 
            Nguyễn Mạnh Hiếu - 2A202600887, 
            Mai Đức Vinh - 2A202600587, 
            Nguyễn Đăng Khương - 2A202600584.
- Provider/model: openrouter / openai/gpt-4o-mini

### Phân công công việc

- Nguyễn Mạnh Hiếu (2A202600887):
    - Chịu trách nhiệm chính về prompt engineering và cập nhật `system_prompt.md`.
    - Viết phần "Reflection" và tổng hợp kết quả thử nghiệm.
    - Kiểm tra và xác nhận các run files đầu ra (`runs/`) và transcript.

- Mai Đức Vinh (2A202600587):
    - Chịu trách nhiệm cấu hình và mô tả tools trong `tools.yaml`.
    - Thực hiện và ghi chép các thay đổi liên quan tới routing và argument cho tools.
    - Chuẩn bị và kiểm thử các case đánh giá nhóm (Group Eval).

- Nguyễn Đăng Khương (2A202600584):
    - Triển khai phần UI demo (`ui/app.py`) và tài liệu hướng dẫn `ui/README.md`.
    - Xử lý phần scripts (như `scripts/parse_runs.py`) và hỗ trợ debug kết nối API.
    - Ghi lại evidence cho Bonus và Live Chat Evidence.

Ghi chú: các nhiệm vụ được phân chia công bằng theo năng lực; mỗi thành viên chịu trách nhiệm chính cho các mục nêu trên nhưng vẫn hỗ trợ chéo khi cần (ví dụ: fix RapidAPI, test Telegram send).

## Final Metrics

- Final version: v3
- Final artifact_version: v3+pa8ca0c40b759+t29bbb44587af
- Best base run file: runs/v3_B_base_openrouter_20260602T123846242430.json
- Base case accuracy: 1.0 (20/20)
- Base tool routing accuracy: 1.0
- Base argument accuracy: 1.0
- Group eval run file: runs/v3_B_group_openrouter_20260602T124231208502.json
- Group eval accuracy: 1.0 (10/10)
- Chat transcript file: transcripts/v3_openrouter_20260602T124026378420.transcript.json

## Version Evidence

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | Đo prompt starter xấu | — | 0.70 | v0_B_base_openrouter_20260602T123152565649.json |
| v1 | system_prompt.md | Clarify/no_tool/send boundary | 0.70 | 0.70 | v1_B_base_openrouter_20260602T123336025846.json |
| v2 | tools.yaml | Mô tả tool chi tiết → routing/args | 0.70 | 1.00 | v2_B_base_openrouter_20260602T123628881196.json |
| v3 | prompt + tools + dedupe | Tool mới + giữ metric | 1.00 | 1.00 | v3_B_base_openrouter_20260602T123846242430.json |

## Failure Analysis (v0 baseline)

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R08, R14 | out_of_scope | send | Gọi send cho bài toán/coding | Prompt: refuse, no tools |
| R10, R11 | missing_info | timeline/fetch đoán | Thiếu handle/URL | Prompt + tools: clarify |
| R12 | wrong_boundary | send | Không hỏi yes_no | tools.yaml clarify yes_no cho Telegram |
| R13 | wrong_tool | lookup thiếu topic news | Args + extra social_search | Rule chỉ dual-tool khi user yêu cầu cả hai |

Sau v2: base eval 20/20 pass.

## Team Eval Cases

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

## Live Chat Evidence

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | Tin AI hôm nay | lookup news day | v3 | Trả lời có nguồn |
| 2 | 5 tweet mới nhất (thiếu handle) | social_search (API 403) | v3 | Không đoán handle |
| 3 | Của Sam Altman | timeline sama | v3 | Đúng handle sau bổ sung |
| 4 | Đăng Telegram | clarify yes_no | v3 | Không send ngay |

## Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| UI (Streamlit) | `ui/app.py`, `ui/README.md` | Chat + tool trace expanders + demo buttons + transcript JSON | Chạy local; refresh reset session; cần `.env` |
| — | — | Chưa làm Telegram send thật | — |

## Reflection

- **system_prompt.md:** scope, clarify rules, one-vs-multiple tools, multi-turn carryover.
- **tools.yaml:** when-to-use per tool; clarify response_type; send confirmation — thay đổi v2 tạo impact lớn nhất (0.7→1.0).
- **Manual review:** subset args (query text) có thể khác nhưng vẫn pass nếu không nằm trong expect subset.
- **Next:** bật Telegram send sau clarify; fix RapidAPI 403 cho timeline live demo.
