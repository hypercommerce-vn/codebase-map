# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Page copy for the Codebase Map website, one dict per language.

Values may contain trusted inline HTML and ``{{placeholders}}`` that
build.py fills with values computed at build time (version, graph stats).
"""

VI = {
    "lang": "vi",
    "meta_title": "Codebase Map — Bản đồ phụ thuộc hàm cho Python và TypeScript",
    "meta_description": (
        "Công cụ mã nguồn mở dựng bản đồ hàm nào gọi hàm nào, cho biết sửa một "
        "chỗ sẽ ảnh hưởng tới đâu trước khi merge. Chạy offline, giấy phép MIT."
    ),
    "skip": "Bỏ qua, tới nội dung chính",
    "nav_label": "Điều hướng chính",
    "nav_use": "Khi nào dùng",
    "nav_how": "Cách hoạt động",
    "nav_demo": "Demo",
    "nav_install": "Cài đặt",
    "menu_label": "Mở menu",
    "copy": "Sao chép",
    "copied": "Đã chép",
    "hero_eyebrow": "Mã nguồn mở · MIT · v{{version}}",
    "hero_title": (
        "Biết sửa một hàm sẽ ảnh hưởng tới đâu, "
        '<span class="hl">trước khi merge</span>.'
    ),
    "hero_lede": (
        "Codebase Map đọc code Python và TypeScript, dựng bản đồ hàm nào gọi "
        "hàm nào, rồi trả lời câu hỏi: đổi chỗ này thì những chỗ nào chịu ảnh "
        "hưởng. Mọi thứ chạy trên máy bạn, code không rời khỏi máy."
    ),
    "cta_demo": "Xem bản đồ mẫu",
    "cta_install": "Hướng dẫn cài",
    "hero_fine": (
        "Cần Python 3.10 trở lên. Không cần tài khoản, không gửi dữ liệu đi đâu."
    ),
    "term_caption": "Output thật: Codebase Map chạy trên chính mã nguồn của nó.",
    "use_title": "Dùng khi nào",
    "use_lede": "Bốn lúc bạn cần biết code đang nối với nhau ra sao.",
    "use1_t": "Trước khi refactor",
    "use1_d": (
        "Liệt kê mọi nơi gọi tới một hàm hay một lớp, sâu tới ba tầng, để biết "
        "vùng ảnh hưởng trước khi sửa."
    ),
    "use2_t": "Khi review PR",
    "use2_d": (
        "So bản chụp trước và sau: hàm thêm, bớt, đổi chữ ký, đổi tên, kèm những "
        "nơi gọi bị kéo theo. Xuất markdown để dán thẳng vào PR."
    ),
    "use3_t": "Khi nhận một dự án mới",
    "use3_d": (
        "Dự án lớn cỡ nào, có những API nào, code nằm ở tầng nào: có câu trả lời "
        "sau vài giây, chưa cần đọc dòng code nào."
    ),
    "use4_t": "Khi làm việc cùng Claude",
    "use4_d": (
        "Máy chủ MCP cho Claude Desktop và Claude Code. Claude tự gọi công cụ tra "
        "bản đồ khi cần, thay vì đoán."
    ),
    "how_title": "Cách hoạt động",
    "how_lede": (
        "Không cơ sở dữ liệu, không dịch vụ chạy nền. Mọi lệnh chỉ đọc một file "
        "<code>graph.json</code>."
    ),
    "how1_t": "Đọc mã nguồn",
    "how1_d": (
        "Parser AST cho Python, parser cho TypeScript/JavaScript (đang thử nghiệm). "
        "Lấy lớp, hàm, method, decorator, lời gọi và import."
    ),
    "how2_t": "Dựng đồ thị",
    "how2_d": (
        "Mỗi hàm là một node, mỗi lời gọi là một cạnh. Tự xếp vào tầng route, "
        "service, model, util, schema, test và nhóm theo module."
    ),
    "how3_t": "Xuất kết quả",
    "how3_d": (
        "<code>graph.json</code> cho máy đọc, <code>index.html</code> tương tác "
        "cho người xem. D3.js đóng gói sẵn, mở được cả khi không có mạng."
    ),
    "how4_t": "Truy vấn và so sánh",
    "how4_d": (
        "summary, query, impact, search, snapshot-diff. Lưu snapshot có nhãn để "
        "so trước và sau một đợt thay đổi."
    ),
    "feat_title": "Tính năng",
    "f1_t": "Bản đồ tương tác, chạy offline",
    "f1_d": (
        "Đồ thị lực D3.js, cây thư mục, minimap, Executive view, PR Diff view và "
        "API Catalog trong một file HTML."
    ),
    "f2_t": "So sánh hai bản chụp",
    "f2_d": (
        "Phát hiện hàm thêm, bớt, đổi chữ ký, đổi tên; liệt kê nơi gọi bị ảnh "
        "hưởng 1–3 tầng. Xuất markdown, JSON hoặc text."
    ),
    "f3_t": "Phạm vi ảnh hưởng của git diff",
    "f3_d": (
        "<code>codebase-map diff main</code> chỉ ra các hàm bạn đã sửa trên nhánh "
        "và những hàm phụ thuộc vào chúng."
    ),
    "f4_t": "Máy chủ MCP cho Claude",
    "f4_d": (
        "Năm công cụ <code>cbm_query</code>, <code>cbm_search</code>, "
        "<code>cbm_impact</code>, <code>cbm_snapshot_diff</code>, "
        "<code>cbm_api_catalog</code>, có cache đồ thị."
    ),
    "f5_t": "Danh mục API và độ phủ test",
    "f5_d": (
        "Liệt kê route API theo method và domain; phủ dữ liệu coverage lên bản "
        "đồ để thấy hàm nào chưa có test."
    ),
    "f6_t": "Mẫu tích hợp CI",
    "f6_d": (
        "Repo có sẵn workflow GitHub Actions lưu baseline khi merge và comment "
        "tác động lên từng PR, dùng làm mẫu cho dự án của bạn."
    ),
    "demo_title": "Một bản đồ thật, ngay trên trang",
    "demo_lede": (
        "Đây là bản đồ Codebase Map vẽ chính mã nguồn của nó, dựng lại mỗi lần "
        "build trang. Kéo để di chuyển, cuộn để phóng to, bấm vào một node để "
        "xem nó gọi ai và ai gọi nó."
    ),
    "demo_activate": "Bấm để tương tác với bản đồ",
    "demo_open": "Mở toàn màn hình",
    "demo_frame_title": "Bản đồ phụ thuộc của mã nguồn Codebase Map",
    "stat_nodes": "hàm, lớp và method",
    "stat_links": "liên kết giữa chúng, vẽ trên bản đồ",
    "stat_edges": "lời gọi và import tìm thấy, gồm cả cái trỏ ra ngoài bản đồ",
    "install_title": "Cài đặt",
    "install_lede": "Chọn cách bạn sẽ dùng. Cả hai đều cài từ PyPI.",
    "tab_cli": "Dòng lệnh",
    "tab_mcp": "Claude (MCP)",
    "cli_step1": "Cài bằng pipx (khuyên dùng) hoặc pip",
    "cli_step2": "Tạo file <code>codebase-map.yaml</code> ở gốc dự án",
    "cli_step3": "Dựng bản đồ, rồi mở <code>docs/function-map/index.html</code>",
    "mcp_step1": "Cài kèm phần MCP",
    "mcp_step2": (
        "Thêm vào <code>claude_desktop_config.json</code> "
        "(macOS: <code>~/Library/Application Support/Claude/</code>)"
    ),
    "mcp_note": (
        "Khởi động lại Claude Desktop là xong. Cấu hình cho Claude Code, Cowork "
        'và cách thử nằm trong <a href="{{repo}}/blob/main/integrations/mcp/'
        'README.md">integrations/mcp/README.md</a>.'
    ),
    "cmd_title": "Các lệnh",
    "cmd_generate": "Dựng đồ thị phụ thuộc",
    "cmd_query": "Tra chi tiết một hàm hoặc lớp",
    "cmd_impact": "Vùng ảnh hưởng của một node",
    "cmd_search": "Tìm node theo từ khoá",
    "cmd_summary": "Thống kê đồ thị",
    "cmd_diff": "Phạm vi ảnh hưởng của git diff",
    "cmd_snapshot_diff": "So sánh hai snapshot",
    "cmd_snapshots": "Quản lý snapshot (list, clean)",
    "cmd_api_catalog": "Liệt kê route API",
    "cmd_coverage": "Phủ dữ liệu độ phủ test lên đồ thị",
    "cmd_check_staleness": "Kiểm tra đồ thị đã cũ so với code chưa",
    "cmd_help": "Mọi lệnh đều có <code>--help</code>.",
    "next_eyebrow": "Đang phát triển",
    "next_title": "Sắp tới: cho người làm app bằng AI mà không đọc code",
    "next_lede": (
        "Bạn nhờ AI sửa app, AI bảo xong, nhưng bạn không chắc có thật không? "
        "Chúng tôi đang làm một phiên bản chạy ngay trong Claude. Sau mỗi lần "
        "sửa, nó báo bằng tiếng Việt thường: AI đã làm gì, có đúng điều bạn yêu "
        "cầu không, có đụng tới thứ đang chạy không."
    ),
    "m1_t": "Chốt yêu cầu",
    "m1_d": (
        "Trước khi AI làm, yêu cầu được nhắc lại thành vài tiêu chí rõ ràng để "
        "bạn bấm chốt."
    ),
    "m2_t": "Báo cáo thay đổi",
    "m2_d": (
        "Sau khi AI làm: đã đổi gì, tiêu chí nào có bằng chứng, có đụng gì ngoài "
        "yêu cầu."
    ),
    "m3_t": "Bản đồ ứng dụng",
    "m3_d": (
        "Lúc nào cũng xem được app gồm những tính năng nào, mỗi tính năng có màn "
        "hình và dữ liệu gì."
    ),
    "next_cta": "Theo dõi trên GitHub Discussions",
    "foot_tagline": (
        "Codebase Map v{{version}} · Giấy phép MIT · Một dự án của Hyper Commerce"
    ),
    "foot_privacy": "Trang này không dùng cookie và không theo dõi người xem.",
    "foot_source": "Mã nguồn",
    "foot_issues": "Báo lỗi",
    "foot_security": "Bảo mật",
}

EN = {
    "lang": "en",
    "meta_title": "Codebase Map — Function dependency graphs for Python and TypeScript",
    "meta_description": (
        "Open-source tool that maps which function calls which, so you know "
        "what a change will touch before you merge. Runs offline, MIT licensed."
    ),
    "skip": "Skip to main content",
    "nav_label": "Main navigation",
    "nav_use": "When to use",
    "nav_how": "How it works",
    "nav_demo": "Demo",
    "nav_install": "Install",
    "menu_label": "Open menu",
    "copy": "Copy",
    "copied": "Copied",
    "hero_eyebrow": "Open source · MIT · v{{version}}",
    "hero_title": (
        'Know what a change will touch, <span class="hl">before you merge</span>.'
    ),
    "hero_lede": (
        "Codebase Map parses Python and TypeScript into a graph of which "
        "function calls which, then answers the question: if I change this, "
        "what else is affected? It all runs on your machine. Your code never "
        "leaves it."
    ),
    "cta_demo": "Explore the live map",
    "cta_install": "Install",
    "hero_fine": "Requires Python 3.10+. No account, no data sent anywhere.",
    "term_caption": "Real output: Codebase Map run on its own source code.",
    "use_title": "When to reach for it",
    "use_lede": "Four moments when you need to know how the code fits together.",
    "use1_t": "Before a refactor",
    "use1_d": (
        "List every caller of a function or class, up to three levels deep, so "
        "you know the blast radius before you touch it."
    ),
    "use2_t": "When reviewing a PR",
    "use2_d": (
        "Compare before and after snapshots: added, removed, re-signatured and "
        "renamed functions, plus the callers they drag along. Export markdown "
        "and paste it into the PR."
    ),
    "use3_t": "When you join a new project",
    "use3_d": (
        "How big it is, which API routes exist, which layer each piece lives "
        "in: answers in seconds, before you read a line of code."
    ),
    "use4_t": "When you work with Claude",
    "use4_d": (
        "An MCP server for Claude Desktop and Claude Code. Claude queries the "
        "graph on its own when it needs to, instead of guessing."
    ),
    "how_title": "How it works",
    "how_lede": (
        "No database, no background service. Every command reads a single "
        "<code>graph.json</code>."
    ),
    "how1_t": "Parse",
    "how1_d": (
        "A Python AST parser and a TypeScript/JavaScript parser (beta) extract "
        "classes, functions, methods, decorators, calls and imports."
    ),
    "how2_t": "Build the graph",
    "how2_d": (
        "Each function is a node, each call an edge. Nodes are sorted into "
        "route, service, model, util, schema and test layers and grouped by "
        "module."
    ),
    "how3_t": "Export",
    "how3_d": (
        "<code>graph.json</code> for machines, an interactive "
        "<code>index.html</code> for people. D3.js is bundled, so it opens "
        "offline."
    ),
    "how4_t": "Query and compare",
    "how4_d": (
        "summary, query, impact, search, snapshot-diff. Save labelled snapshots "
        "to compare before and after a batch of changes."
    ),
    "feat_title": "Features",
    "f1_t": "Interactive map, works offline",
    "f1_d": (
        "D3.js force graph, file tree, minimap, Executive view, PR Diff view and "
        "API Catalog in a single HTML file."
    ),
    "f2_t": "Dual-snapshot diff",
    "f2_d": (
        "Finds added, removed, re-signatured and renamed functions and lists "
        "the callers affected 1–3 levels out. Markdown, JSON or text output."
    ),
    "f3_t": "Git diff impact",
    "f3_d": (
        "<code>codebase-map diff main</code> shows the functions you changed on "
        "your branch and everything that depends on them."
    ),
    "f4_t": "MCP server for Claude",
    "f4_d": (
        "Five tools, <code>cbm_query</code>, <code>cbm_search</code>, "
        "<code>cbm_impact</code>, <code>cbm_snapshot_diff</code> and "
        "<code>cbm_api_catalog</code>, backed by a graph cache."
    ),
    "f5_t": "API catalog and test coverage",
    "f5_d": (
        "List API routes by method and domain; overlay coverage data on the map "
        "to see which functions have no tests."
    ),
    "f6_t": "CI templates",
    "f6_d": (
        "The repo ships GitHub Actions workflows that save a baseline on merge "
        "and comment the impact on every PR, ready to adapt to your project."
    ),
    "demo_title": "A real map, right on this page",
    "demo_lede": (
        "This is Codebase Map's own source code, mapped by Codebase Map and "
        "rebuilt every time the site is built. Drag to pan, scroll to zoom, "
        "click a node to see what it calls and what calls it."
    ),
    "demo_activate": "Click to interact with the map",
    "demo_open": "Open full screen",
    "demo_frame_title": "Dependency map of the Codebase Map source code",
    "stat_nodes": "functions, classes and methods",
    "stat_links": "links between them, drawn on the map",
    "stat_edges": "calls and imports found, including ones that point off the map",
    "install_title": "Install",
    "install_lede": "Pick how you will use it. Both install from PyPI.",
    "tab_cli": "Command line",
    "tab_mcp": "Claude (MCP)",
    "cli_step1": "Install with pipx (recommended) or pip",
    "cli_step2": "Create <code>codebase-map.yaml</code> in your project root",
    "cli_step3": "Build the map, then open <code>docs/function-map/index.html</code>",
    "mcp_step1": "Install with the MCP extra",
    "mcp_step2": (
        "Add it to <code>claude_desktop_config.json</code> "
        "(macOS: <code>~/Library/Application Support/Claude/</code>)"
    ),
    "mcp_note": (
        "Restart Claude Desktop and you are done. Setup for Claude Code and "
        'Cowork, plus a test prompt, is in <a href="{{repo}}/blob/main/'
        'integrations/mcp/README.md">integrations/mcp/README.md</a>.'
    ),
    "cmd_title": "Commands",
    "cmd_generate": "Generate the dependency graph",
    "cmd_query": "Look up a function or class",
    "cmd_impact": "Impact zone of a node",
    "cmd_search": "Search nodes by keyword",
    "cmd_summary": "Graph statistics",
    "cmd_diff": "Impact of a git diff",
    "cmd_snapshot_diff": "Compare two snapshots",
    "cmd_snapshots": "Manage snapshots (list, clean)",
    "cmd_api_catalog": "List API routes",
    "cmd_coverage": "Overlay test coverage on the graph",
    "cmd_check_staleness": "Check whether the graph is behind the code",
    "cmd_help": "Every command supports <code>--help</code>.",
    "next_eyebrow": "In development",
    "next_title": "Coming next: for people who build apps with AI but don't read code",
    "next_lede": (
        "You ask an AI to change your app, it says it's done, but you can't "
        "tell if that's true. We are building a version that runs inside "
        "Claude. After every change it tells you, in plain words, what the AI "
        "did, whether it matches what you asked for, and whether it touched "
        "anything that already worked."
    ),
    "m1_t": "Lock the request",
    "m1_d": (
        "Before the AI starts, your request is restated as a few clear "
        "acceptance criteria for you to confirm."
    ),
    "m2_t": "Change report",
    "m2_d": (
        "After the AI finishes: what changed, which criteria have evidence, and "
        "what it touched outside the request."
    ),
    "m3_t": "App map",
    "m3_d": (
        "Any time, see which features your app has and which screens and data "
        "each one uses."
    ),
    "next_cta": "Follow along on GitHub Discussions",
    "foot_tagline": (
        "Codebase Map v{{version}} · MIT License · A Hyper Commerce project"
    ),
    "foot_privacy": "This site sets no cookies and does not track visitors.",
    "foot_source": "Source",
    "foot_issues": "Report a bug",
    "foot_security": "Security",
}

STRINGS = {"vi": VI, "en": EN}
