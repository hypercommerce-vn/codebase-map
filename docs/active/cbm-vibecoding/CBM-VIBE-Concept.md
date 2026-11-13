# CBM-VIBE — Concept v0.1

> **Trạng thái:** CEO duyệt nội dung ngày 13/11/2026 · "CBM-VIBE" là tên tạm
> **Design preview:** [CBM-VIBE-Design-Preview.html](CBM-VIBE-Design-Preview.html) · **Khảo sát khách:** [CBM-VIBE-Khao-Sat-Khach.md](CBM-VIBE-Khao-Sat-Khach.md)

## Người dùng

Người tự làm phần mềm bằng AI nhưng không chuyên IT: chưa từng mở terminal, hoặc từng mở nhưng là tay mơ, tự học qua mạng. Họ không đọc được code, không cài công cụ dòng lệnh, không sửa file cấu hình. Họ nghĩ theo tính năng, màn hình và dữ liệu.

## Vấn đề, theo lời họ

- "AI sửa cái này thì hỏng cái kia."
- "AI bảo xong rồi, nhưng tôi không biết có thật không."
- "Tôi không biết app của mình gồm những gì."
- "Càng sửa càng rối."

## Lời hứa

Sau mỗi lần nhờ AI sửa, người dùng biết ba điều bằng tiếng Việt thường: AI đã làm gì, có đúng điều mình yêu cầu không, và có đụng tới thứ đang chạy không.

## Mô hình: một chuỗi, ba khoảnh khắc

CBM nối và kiểm chứng một chuỗi: **Yêu cầu (tiêu chí nghiệm thu) → Màn hình và dữ liệu → Code → Bằng chứng.** BA, design và testing không thành ba module riêng. Chúng thành ba khoảnh khắc trong vòng lặp người dùng vốn đang làm:

| Khoảnh khắc | Người dùng thấy | CBM tính từ code |
|---|---|---|
| Trước khi AI làm: **Chốt yêu cầu** | AI nhắc lại yêu cầu thành 2–4 tiêu chí nghiệm thu; người dùng bấm chốt | Tính năng, màn hình, dữ liệu sẽ bị đụng tới; lưu trạng thái "trước" |
| Sau khi AI làm: **Báo cáo thay đổi** | Đã làm gì; tiêu chí nào có bằng chứng; đụng gì ngoài yêu cầu | So sánh trước–sau, quy mọi thay đổi về tính năng, đánh dấu bằng chứng hết hạn |
| Bất cứ lúc nào: **Bản đồ ứng dụng** | Danh sách tính năng; mỗi tính năng gồm màn hình nào, dữ liệu nào, tình trạng ra sao | Graph, nhóm nghiệp vụ, danh mục API, code không thuộc tính năng nào |

Mỗi tiêu chí có đúng ba trạng thái:

- **Có bằng chứng** — kiểm thử tự động đậu và chạm đúng code của tính năng, hoặc người dùng tự bấm thử theo hướng dẫn.
- **Cần kiểm lại** — code liên quan đã đổi sau lần kiểm cuối.
- **Chưa kiểm** — chưa có bằng chứng nào.

Bằng chứng tự hết hạn khi code đổi. Đây là phần cần đến graph: biết code nào thuộc tính năng nào, và thay đổi nào lan tới nó.

## Nguyên tắc

1. Người dùng không chạy lệnh, không sửa cấu hình. AI vận hành CBM thay họ.
2. Tầng mặc định không có tên hàm, tên file hay phần trăm. Thuật ngữ chỉ xuất hiện khi người dùng bấm xuống sâu, kèm một dòng giải thích.
3. Tách rõ phần CBM tính từ code và phần AI diễn đạt. CBM không nói "đúng", chỉ nói "có bằng chứng".
4. Kiểm soát trước, học sau. Người dùng học qua bốn tầng của chính app mình (tính năng → màn hình và dữ liệu → luồng xử lý → code), không qua giáo trình.

## Đã có và phải làm mới

**Dùng lại:** `snapshot-diff`, `impact`, `coverage`, `api-catalog`, config `domains` (CM-S4-01, PR #145), Executive view, MCP server, và nội dung skill cùng các lệnh của 3 plugin. Phần đóng gói plugin phải làm lại, xem mục "Đóng gói trên Claude". `snapshot-diff` hiện chỉ thấy hàm thêm, bớt và đổi chữ ký, không thấy sửa nội dung; xem mục "So sánh trực tiếp trên app mẫu".

**Làm mới:** nơi lưu tính năng và tiêu chí nghiệm thu; ba trạng thái bằng chứng; nhận diện màn hình và component trong parser TS (hiện trang xếp chung với API vào ROUTER, component vào UTIL); lớp trình bày tiếng Việt thường; cài đặt không cần terminal.

**Không làm ở v1:** sinh code, chấm thẩm mỹ giao diện, thêm ngôn ngữ như Java hay Go, giáo trình học lập trình.

## Quyết định

1. **Kênh tiếp cận — CEO chốt 12/11: Claude.** Khách vibecode bằng Claude, nên đi theo lựa chọn (a). Hai lựa chọn còn lại giữ để tham khảo:
   - (a) **Đã chọn.** Nằm trong Claude, qua plugin/skill. Đủ cả ba khoảnh khắc. Phải bỏ bước cài bằng `pipx`.
   - (b) Trang web nối GitHub. Tới được mọi nền tảng, không cài gì. Thiếu khoảnh khắc "chốt yêu cầu", và phải vận hành một dịch vụ giữ code của khách.
   - (c) Trang kéo-thả chạy ngay trong trình duyệt. Không cài, không máy chủ, code không rời máy. Chỉ làm được bản đồ. Khả thi về nguyên tắc vì CBM lõi chỉ phụ thuộc PyYAML; cần thử 1–2 ngày để xác nhận.

   Cách đóng gói và những gì còn phải xác định: xem mục "Đóng gói trên Claude".
2. **QD-02 trên bảng điều hành — CEO chốt 13/11: CM-S4 đi trước** (PR #145), vì `domains` là nơi lưu "tính năng". Phần LANG: JS/TS/React vẫn cần vì người vibecoding dùng chúng; Java lùi lại.
3. **Còn mở: quan hệ với Open Core.** Handbook training hiện nhắm tổ chức có đội kỹ sư, sản phẩm và kinh doanh. CBM-VIBE nhắm cá nhân không chuyên, nên là dòng sản phẩm thứ hai với kênh và giá riêng.

## Đóng gói trên Claude

Đối chiếu với tài liệu chính thức của Claude ngày 12/11/2026 (nguồn ở cuối mục).

| Thành phần của plugin | Chat | Cowork | Claude Code (terminal, VS Code, tab Code của app máy tính) |
|---|---|---|---|
| Skill | Có | Có | Có |
| Hook (tự chạy theo sự kiện) | Bị bỏ qua | Có | Có |
| Mod (khung bên cạnh cuộc trò chuyện, có nút bấm) | Không | Không | Có |
| MCP server chạy trên máy | Bị bỏ qua | Có, khi phiên chạy trên máy | Có |
| Thư mục `bin/` trong plugin | Không cài được | Không cài được | Có |

**CEO chốt 12/11: đóng gói theo ba tầng, làm tầng skill trước**, để không phụ thuộc vào việc khách dùng bề mặt nào.

- **Tầng 1, skill:** nạp được ở cả ba nơi.
- **Tầng 2, hook:** thêm báo cáo tự động ở Cowork và Claude Code.
- **Tầng 3, mod:** thêm khung bên cạnh cuộc trò chuyện ở Claude Code.

Người dùng cài plugin bằng giao diện (Customize > Plugins: thêm marketplace từ GitHub hoặc tải file zip), không cần terminal.

Ba khoảnh khắc ứng với điểm mở rộng nào:

- **Chốt yêu cầu:** skill hướng dẫn Claude nhắc lại yêu cầu thành tiêu chí và hỏi xác nhận bằng nút bấm. Hook `UserPromptSubmit` hoặc `PreToolUse` (trước lần sửa file đầu tiên) lưu trạng thái "trước".
- **Báo cáo thay đổi:** hook `Stop` chạy khi Claude làm xong một lượt, gọi `snapshot-diff` rồi đưa kết quả cho Claude trình bày. Nhờ hook, báo cáo luôn xuất hiện, không phụ thuộc việc AI có nhớ hay không.
- **Bản đồ ứng dụng:** một mod vẽ khung bên cạnh cuộc trò chuyện, tự cập nhật sau mỗi lượt. Phương án dự phòng: trang HTML mở trong khung Browser của app.

**Plugin CBM hiện tại không theo định dạng chuẩn.** Claude đọc `.claude-plugin/plugin.json`, `.mcp.json` và `hooks/hooks.json`. Plugin của mình dùng `manifest.json`, `mcp/config.json` và `hooks/post-install.sh`, trong khi định dạng plugin không có script nào chạy lúc cài. Hệ quả theo tài liệu (chưa cài thử): skill và 3 lệnh vẫn được nạp vì nằm đúng thư mục mặc định, nhưng MCP server không được nối và không có gì tự cài gói `codebase-map`. Trên máy CEO, các lệnh `/cbm-*` đang chạy từ bản copy tay trong `~/.claude/`, không phải từ plugin.

**Phần máy chạy CBM: kết quả thử ngày 12/11 trên máy CEO.** Mã nguồn CBM chạy được bằng Python 3.9.6 có sẵn của macOS, không cài gì, không có PyYAML, không có file cấu hình. Đồ thị ra giống hệt bản chạy trên Python 3.14 (201 node, 998 cạnh). Phép thử mới chạy parser Python trên chính mã nguồn CBM; parser TS chưa thử trên Python 3.9. Lõi cần sửa hai chỗ: cho PyYAML thành tuỳ chọn, và thêm chế độ không cần file cấu hình (lệnh `generate` hiện từ chối chạy khi thiếu file này).

**Rủi ro còn lại: máy khách có Python hay không.** Mac chỉ có khi đã cài Command Line Tools, Windows mặc định không có, và tài liệu của Claude không nói rõ sandbox của Chat hay môi trường của Cowork có Python. Ba hướng:

1. **Đã chọn cho tầng 1.** Đóng gói mã nguồn CBM trong skill, chạy bằng Python có sẵn. Khi máy không có Python, skill vẫn làm phần "chốt yêu cầu" và ghi rõ báo cáo chưa được kiểm chứng bằng máy.
2. Đóng gói bản chạy sẵn, không cần Python. Không viết lại gì; phải build riêng cho từng hệ điều hành.
3. Viết lại phần phân tích TS/JS bằng JavaScript, chạy ngay trong mod. Không phụ thuộc gì trên máy khách; tốn công nhất, nhưng cũng là dịp thay parser TS dạng regex hiện nay.

### Phạm vi tầng 1 (CEO duyệt 13/11/2026)

Ước lượng 8 SP (VIBE-102 được thêm sau phép thử ngày 13/11). Mỗi việc một PR từ nhánh riêng, qua review gate. Chưa nằm trong tầng 1: nối màn hình với component (JSX) và component với API (`fetch`).

| Mã | Việc | Xong khi | SP |
|---|---|---|---|
| VIBE-101 | Lõi chạy không cần cài: PyYAML tuỳ chọn; chế độ không cần file cấu hình, tự nhận thư mục nguồn và ngôn ngữ | `generate` chạy trên Python 3.9 không có PyYAML, cho một dự án Python mẫu và một dự án TS mẫu; có test tự động | 1,5 |
| VIBE-102 | Phát hiện thay đổi theo nội dung: so nội dung từng file và từng hàm; parser TS ghi được dòng kết thúc của hàm và nhận được hàm generic | Trên app mẫu `so-dat-lich`, báo đúng `lib/reminders.ts` bị sửa và hai hàm truy cập dữ liệu xuất hiện trong đồ thị; có test tự động | 2 |
| VIBE-103 | Kho tính năng, tiêu chí, bằng chứng (một file trong dự án); quy thay đổi về tính năng; đánh dấu bằng chứng hết hạn | Từ hai snapshot trước–sau của app mẫu, ra đúng "Đặt lịch và Nhắc lịch bị đụng" và danh sách tiêu chí cần kiểm lại | 2 |
| VIBE-104 | Plugin `cbm-vibe` đúng định dạng chuẩn; skill tiếng Việt cho ba khoảnh khắc ở dạng chữ trong chat; mã nguồn CBM kèm trong skill | `claude plugin validate` đạt; chạy trọn vòng "chốt yêu cầu → báo cáo thay đổi" trên dự án mẫu | 1,5 |
| VIBE-105 | Cài thử qua giao diện ở Chat, Cowork và tab Code trên máy CEO | Có bảng ghi rõ nơi nào chạy đủ, nơi nào thiếu gì | 1 |

Nguồn: [Plugin manifest reference](https://code.claude.com/docs/en/plugins/manifest-reference) · [Plugin feature support across platforms](https://claude.com/docs/plugins/platform-support) · [Mods overview](https://code.claude.com/docs/en/plugins/mods/overview) · [Hooks](https://code.claude.com/docs/en/hooks)

## Số liệu tham khảo (tra ngày 12/11/2026)

Không có thống kê công khai nào chia người vibecode bằng Claude theo tab Code, Cowork và Chat. Anthropic không công bố số người dùng theo từng bề mặt. Các số gần nhất, mỗi nguồn đo một thứ khác nhau nên không so trực tiếp được:

| Bề mặt | Số liệu | Nguồn |
|---|---|---|
| Chat | 35% cuộc trò chuyện thuộc nhóm nghề máy tính và toán; tỉ lệ đang giảm vì việc code chuyển sang API, nơi Claude Code chiếm tỉ trọng lớn | [Economic Index 3/2026](https://www.anthropic.com/research/economic-index-march-2026-report), dữ liệu 5–12/2/2026 |
| Chat + Cowork gộp | Khoảng 1/6 cuộc trò chuyện là code và việc kỹ thuật (app, script) | [Economic Index 6/2026](https://www.anthropic.com/research/economic-index-june-2026-report), dữ liệu 10/4–10/6/2026 |
| Cowork | 8,7% phiên là phát triển phần mềm | [How people are using Claude Cowork](https://claude.com/es/resources/articles/how-people-are-using-claude-cowork), 1,2 triệu phiên, 11–31/5/2026 |
| Claude Code (gộp terminal, web, app máy tính) | Không có tỉ lệ theo bề mặt. Nhóm ngoài ngành phần mềm tăng nhanh nhất là quản lý, bán hàng, pháp lý (không kèm con số) | [Nghiên cứu Claude Code của Anthropic](https://www.anthropic.com/research/claude-code-expertise), khoảng 400.000 phiên, 10/2025–4/2026 |

Khảo sát bên ngoài, mẫu nhỏ:

- 200 người làm marketing và bán hàng đã dùng Claude Code hoặc Cowork: sản phẩm dùng chính là Cowork 32%, Code 31%, Chat 30% ([Growth Unhinged](https://www.growthunhinged.com/p/2026-claude-code-gtm-report), 3–4/2026).
- 818 người Mỹ đã tự làm công cụ bằng AI: 34% không có nền lập trình; nhóm này dùng chatbot chung 82%, trợ lý trong công cụ code 71%, phần mềm code AI chuyên dụng 40%; 92% từng gặp trở ngại lớn, trong đó lỗi code 38%, lo ngại bảo mật 37% ([Zapier/Centiment](https://stacker.com/stories/ai/34-people-shipping-software-using-ai-tools-have-no-formal-programming-background), 5/2026).
- 162 người vibecode: 5,6% người không phải lập trình viên dùng Claude, so với 27,8% lập trình viên chuyên nghiệp; ChatGPT là 77,8%. Người không chuyên hay nhờ AI làm lại thay vì tìm lỗi, và là nhóm duy nhất có người không bao giờ kiểm tra code ([arXiv 2605.24521](https://arxiv.org/html/2605.24521), 5/2026).

Số liệu ủng hộ luận điểm sản phẩm: trong Claude Code, phiên của người mới chỉ đạt kết quả được kiểm chứng ở 15% số phiên, so với 28–33% ở người có kinh nghiệm, và bị bỏ dở ở 19% số phiên gặp trục trặc, so với 5–7%.

Vì chưa biết khách chia theo bề mặt thế nào, đóng gói nên theo ba tầng: skill chạy ở cả ba nơi; hook thêm báo cáo tự động ở Cowork và Claude Code; mod thêm khung bên cạnh ở Claude Code.

## Sản phẩm tương tự (tra ngày 12–13/11/2026)

Chưa tìm thấy sản phẩm nào, ở quốc tế hay Việt Nam, làm trọn cả ba khoảnh khắc cho người tự làm một mình, không có kỹ sư duyệt hộ. Từng mảng thì đều đã có người làm. Đánh giá dưới đây dựa trên tài liệu công khai, chưa dùng thử.

| Nhóm | Ví dụ | Họ làm được gì | Khác CBM-VIBE ở đâu |
|---|---|---|---|
| Bản đồ code bằng lời thường | [Understand Anything](https://github.com/Egonex-AI/Understand-Anything) (92.269 sao GitHub, MIT), Graphify, CodeGraph, Grapuco | Đồ thị tương tác, tóm tắt bằng lời thường, tour hướng dẫn, phân tích ảnh hưởng của thay đổi (`/understand-diff`), giao diện đổi theo người xem kể cả PM, góc nhìn nghiệp vụ, có tiếng Việt | Không có tiêu chí nghiệm thu, không theo dõi bằng chứng, không đối chiếu thay đổi với yêu cầu. Đồ thị do nhiều agent AI dựng nên tốn token |
| Chốt yêu cầu trước khi AI code | Kiro, GitHub Spec Kit, OpenSpec, BMAD, Traycer | Biến yêu cầu thành spec và tiêu chí; Traycer đối chiếu code với kế hoạch | Cho lập trình viên, nặng quy trình; việc đối chiếu do AI làm |
| Kiểm thử cho app vibecode | TestSprite, Autonoma, Shiplight, testRigor | Sinh và chạy test từ yêu cầu hoặc code; TestSprite nhắm cả PM và founder | Tạo bằng chứng tốt hơn CBM vì chạy app thật. Không cho biết AI đụng gì ngoài yêu cầu, không có bản đồ |
| Quét bảo mật, chấm điểm sẵn sàng ra mắt | Brek, Vibe App Scanner, VibeEval, Replit Security Agent | Quét app đã triển khai, cho điểm, đưa câu lệnh sửa để dán lại cho AI | Chỉ nhìn bảo mật từ bên ngoài; không gắn với yêu cầu hay thay đổi |
| Người không chuyên sửa app có sẵn | Khoảng 40 công cụ: Ovren, Revyse, Specship, Kosuke | Bản sao an toàn, xem trước, PR kèm báo cáo thay đổi | Cổng chất lượng là một kỹ sư duyệt PR. Khách của CBM-VIBE không có kỹ sư |
| Tính năng có sẵn của Claude | Plan mode, checkpoint, `/code-review`, output style Explanatory, mod mẫu `blast-radius` và `replay-theater` | Hỏi trước khi sửa, quay lui, tìm lỗi, giải thích | Nói bằng ngôn ngữ lập trình viên; không có tiêu chí, bằng chứng hay kết luận cho người không chuyên |

**Việt Nam:** không tìm thấy sản phẩm Việt nào làm việc này. Grapuco gần nhất (đồ thị code và Spec Agent sinh use case, acceptance criteria), nhắm từ solo founder tới doanh nghiệp, không có tính năng riêng cho người không biết code; trang không ghi pháp nhân hay quốc gia, bảng giá không đọc được. Phần còn lại là khoá học vibe coding (Cole.vn, FUNiX, các khoá tiếng Việt trên Inflearn).

**Hệ quả cho thiết kế:**

1. Chỗ còn trống là sợi dây nối yêu cầu, thay đổi và bằng chứng cho người không có kỹ sư. Dồn sức vào khoảnh khắc 1 và 2.
2. Bản đồ ứng dụng không còn là điểm khác biệt. Lùi tầng 3 (mod); bản đồ của mình chỉ cần là bảng trạng thái tiêu chí theo tính năng.
3. Lợi thế kỹ thuật của CBM là tất định, nhanh và không tốn token, nên chạy được sau mỗi lượt sửa.
4. Không tự làm sinh test hay quét bảo mật. Nhận kết quả từ công cụ khác làm bằng chứng.
5. Rủi ro: Anthropic thêm sẵn tính năng tương tự; Understand Anything thêm tiêu chí và bằng chứng.

Nguồn: [Understand Anything](https://github.com/Egonex-AI/Understand-Anything) · [bài BetterStack](https://betterstack.com/community/guides/ai/understand-anything/) · [danh sách 40 công cụ](https://dev.to/butterneck/ai-tools-that-let-non-developers-change-an-existing-web-app-2026-1pcp) · [TestSprite](https://www.testsprite.com/blog/no-code-qa-how-non-technical-teams-are-owning-software-quality-in-2026) · [công cụ spec-driven](https://codemyspec.com/blog/best-spec-driven-development-tools) · [Traycer](https://docs.traycer.ai/tasks/verification) · [Brek](https://brek.lovable.app/) · [Grapuco](https://www.grapuco.com/vi)

## So sánh trực tiếp trên app mẫu (13/11/2026)

App mẫu: `tests/fixtures/so-dat-lich/` (Next.js, 26 file TS/TSX, 5 tính năng), kèm bộ thay đổi `change-huy-lich` mô phỏng yêu cầu "cho khách tự huỷ lịch trước 2 tiếng". Bộ thay đổi cố ý chứa một chỗ ngoài yêu cầu: AI đổi thời điểm nhắc lịch từ 24 giờ xuống 12 giờ và sửa lời nhắn.

**CBM (đã chạy thật):**

- Dựng đồ thị trong 16 ms: 44 hàm, gán đúng vào 5 tính năng qua `domains`.
- Thấy được phụ thuộc giữa tính năng: Nhắc lịch gọi sang Đặt lịch và Danh sách khách.
- Không thấy hai hàm truy cập dữ liệu vì chúng dùng generic (`readAll<K>`, `insertRow<K>`), nên không biết tính năng nào dùng dữ liệu nào.
- Không nối màn hình với component (JSX) và component với API (`fetch`), nên màn hình, component và phần xử lý là ba cụm rời.
- `snapshot-diff` báo 7 hàm thêm, 0 hàm sửa. Nó bỏ sót toàn bộ thay đổi ở Nhắc lịch, vì chỉ coi hàm là bị sửa khi đổi tham số, kiểu trả về, decorator hoặc lớp cha. Parser TS cũng không ghi dòng kết thúc của hàm.
- Thử nghiệm so nội dung theo file (viết nhanh ngoài mã nguồn): bắt được `lib/reminders.ts` bị đổi và quy đúng về Nhắc lịch.

**Understand Anything (đọc mã nguồn công khai, chưa chạy):**

- Phân tích cấu trúc bằng tree-sitter cho hơn 10 ngôn ngữ, có hướng dẫn riêng cho Next.js và React.
- Lưu dấu vân tay nội dung từng file (`contentHash`) và phân loại thay đổi thành không đổi, bề mặt, cấu trúc.
- `/understand-diff` lấy danh sách file đổi từ git, tìm node tương ứng và các node cách một bước, rồi để AI viết phân tích. Vì đi từ git nên `lib/reminders.ts` chắc chắn nằm trong danh sách file đổi.
- Cần Node. Khi cài, plugin thêm hai hook: một chạy sau mỗi lệnh Bash, một chạy lúc mở phiên.

**Kết luận:** với bộ máy hiện tại, CBM sẽ nói "AI chỉ đụng Đặt lịch", tức báo an toàn sai. Phải thêm phát hiện thay đổi theo nội dung trước khi làm bất cứ báo cáo nào cho người dùng; việc này là VIBE-102 trong bảng việc tầng 1.

Để chạy Understand Anything, đã tạo cục bộ một bản git độc lập của app mẫu (một commit gốc, bộ thay đổi ở dạng chưa commit); bản này không nằm trong repo.

## Giả định rủi ro nhất và cách thử rẻ nhất

**Giả định:** người không đọc được code vẫn hiểu báo cáo này và làm theo.

**Cách thử, không cần viết code mới:** chọn 5 người đúng chân dung, lấy app thật của họ, đội mình chạy CBM rồi soạn tay báo cáo theo mẫu trong design preview. Đạt nếu ít nhất 4/5 người kể lại đúng AI vừa làm gì và tự làm được một việc kiểm tra.
