# HC-AI | ticket: FDD-TOOL-CODEMAP
"""HTML Exporter — interactive D3.js force-directed graph visualization."""
from __future__ import annotations

import json
from pathlib import Path

from codebase_map.graph.models import Graph

# HC-AI | ticket: FDD-TOOL-CODEMAP
_D3_BUNDLE_PATH = Path(__file__).parent / "d3.v7.min.js"


def _load_d3_bundle() -> str:
    """Load bundled D3.js — offline-capable, no CDN."""
    if _D3_BUNDLE_PATH.exists():
        return _D3_BUNDLE_PATH.read_text(encoding="utf-8")
    # Fallback: CDN (should not happen in production)
    return ""


def export_html(graph: Graph, output_path: str | Path) -> Path:
    """Export graph as interactive HTML with D3.js visualization."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    graph_data = json.dumps(graph.to_dict(), ensure_ascii=False)
    d3_code = _load_d3_bundle()

    html = _build_html(graph_data, graph.project, d3_code)

    with open(path, "w", encoding="utf-8") as f:
        f.write(html)

    mode = "bundled" if d3_code else "CDN fallback"
    print(f"[OK] HTML exported: {path} (D3: {mode})")
    return path


def _build_html(graph_json: str, project_name: str, d3_code: str = "") -> str:
    """Build the complete HTML visualization page.

    HC-AI | ticket: FDD-TOOL-CODEMAP
    CM-S1 Day 2: top bar (CM-S1-10), sidebar tree (CM-S1-01),
    empty state + accessibility (CM-S1-09).
    CM-S1 Day 3: domain clustering (CM-S1-02).
    CM-S1 Day 4: minimap (CM-S1-06), toolbar (CM-S1-07),
    dual legend (CM-S1-08).
    """
    if d3_code:
        d3_script = f"<script>{d3_code}</script>"
    else:
        d3_script = '<script src="https://d3js.org/d3.v7.min.js"></script>'
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Codebase Map — {project_name}</title>
<style>
/* HC-AI | ticket: FDD-TOOL-CODEMAP */
:root {{
  --hc-primary: #6366f1;
  --bg-canvas: #0d1117;
  --bg-surface: #161b22;
  --bg-surface-hover: #1c2128;
  --bg-elevated: #21262d;
  --border: #30363d;
  --border-focus: #58a6ff;
  --text-primary: #e6edf3;
  --text-secondary: #8b949e;
  --text-muted: #484f58;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: var(--bg-canvas); color: var(--text-primary); overflow: hidden; }}

/* CM-S1-10: Top bar */
#topbar {{
  height: 48px; background: var(--bg-surface);
  border-bottom: 1px solid var(--border);
  display: flex; align-items: center; padding: 0 16px; gap: 12px;
}}
#topbar .logo-icon {{
  width: 28px; height: 28px; background: var(--hc-primary);
  border-radius: 6px; display: flex; align-items: center;
  justify-content: center; font-size: 14px; font-weight: 700; color: #fff;
  flex-shrink: 0;
}}
#topbar .logo-text {{ font-size: 14px; font-weight: 600; }}
#topbar .logo-ver {{
  font-size: 11px; color: var(--text-muted);
  background: var(--bg-elevated); padding: 2px 6px; border-radius: 4px;
}}
.stat-badge {{
  font-size: 11px; color: var(--text-secondary);
  background: var(--bg-canvas); padding: 4px 10px;
  border-radius: 12px; border: 1px solid var(--border);
}}
.stat-badge strong {{ color: var(--text-primary); }}
#topbar .timestamp {{
  font-size: 11px; color: var(--text-muted); margin-left: auto;
}}

/* Layout */
#app {{ display: flex; flex-direction: column; height: 100vh; }}
#main {{ display: flex; flex: 1; overflow: hidden; }}

/* CM-S1-01: Sidebar */
#sidebar {{
  width: 340px; background: var(--bg-surface);
  border-right: 1px solid var(--border);
  display: flex; flex-direction: column; overflow: hidden; flex-shrink: 0;
}}
#graph-container {{ flex: 1; position: relative; }}

/* Search */
.sidebar-search {{ padding: 12px; border-bottom: 1px solid var(--border); }}
#search-box {{
  width: 100%; padding: 8px 12px 8px 34px;
  background: var(--bg-canvas); border: 1px solid var(--border);
  border-radius: 8px; color: var(--text-primary); font-size: 13px;
  outline: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='%238b949e' viewBox='0 0 24 24'%3E%3Cpath d='M15.5 14h-.79l-.28-.27A6.47 6.47 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z'/%3E%3C/svg%3E");
  background-repeat: no-repeat; background-position: 10px center;
}}
#search-box:focus {{ border-color: var(--border-focus); }}
#search-result-count {{
  font-size: 11px; color: var(--text-muted);
  padding: 4px 12px; display: none;
}}

/* Layer filter chips */
.filters {{
  padding: 8px 12px; border-bottom: 1px solid var(--border);
  display: flex; gap: 4px; flex-wrap: wrap;
}}
.chip {{
  display: inline-flex; align-items: center; gap: 4px;
  padding: 3px 10px; font-size: 11px; border-radius: 12px;
  border: 1px solid var(--border); background: transparent;
  color: var(--text-secondary); cursor: pointer;
}}
.chip.active {{ background: var(--hc-primary); border-color: var(--hc-primary); color: #fff; }}
.chip .dot {{ width: 6px; height: 6px; border-radius: 50%; }}
.chip .count {{ font-size: 11px; opacity: .7; }}

/* Domain tree */
#domain-tree {{ flex: 1; overflow-y: auto; padding: 6px; }}
.domain-header {{
  display: flex; align-items: center; gap: 8px;
  padding: 6px 8px; border-radius: 6px; cursor: pointer;
  font-size: 12px; font-weight: 600; color: var(--text-primary);
}}
.domain-header:hover {{ background: var(--bg-surface-hover); }}
.domain-header .arrow {{
  font-size: 11px; color: var(--text-muted);
  width: 16px; text-align: center; transition: transform .15s;
  display: inline-block; flex-shrink: 0;
}}
.domain-header .arrow.open {{ transform: rotate(90deg); }}
.domain-header .domain-dot {{ width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }}
.domain-header .domain-count {{
  font-size: 11px; color: var(--text-muted); margin-left: auto;
  background: var(--bg-canvas); padding: 1px 6px; border-radius: 8px;
}}
.domain-children {{ padding-left: 16px; display: none; }}
.domain-children.open {{ display: block; }}
.node-item {{
  padding: 5px 8px; border-radius: 4px; cursor: pointer;
  font-size: 12px; display: flex; align-items: center; gap: 6px;
}}
.node-item:hover {{ background: var(--bg-surface-hover); }}
.node-item.selected {{
  background: rgba(99,102,241,.15); border-left: 2px solid var(--hc-primary);
}}
.node-item .type-icon {{ font-size: 11px; width: 18px; text-align: center; flex-shrink: 0; }}
.node-item .node-name {{ color: var(--text-primary); font-weight: 500; }}
.node-item .node-layer {{ font-size: 11px; color: var(--text-muted); margin-left: auto; }}
.method-item {{
  font-size: 11px; padding: 3px 8px 3px 28px;
  color: var(--text-secondary); cursor: pointer; border-radius: 4px;
}}
.method-item:hover {{ background: var(--bg-surface-hover); color: var(--text-primary); }}
.method-item.selected {{ color: var(--hc-primary); font-weight: 600; }}
.class-children {{ display: none; }}
.class-children.open {{ display: block; }}

/* CM-S1-09: Empty state */
.empty-state {{
  text-align: center; padding: 32px 16px;
}}
.empty-state .es-icon {{ font-size: 28px; margin-bottom: 6px; opacity: .5; }}
.empty-state .es-title {{ font-size: 13px; color: var(--text-secondary); margin-bottom: 4px; }}
.empty-state .es-hint {{ font-size: 11px; color: var(--text-muted); }}

/* Detail panel */
#detail-panel {{
  position: absolute; top: 16px; right: 16px; width: 380px;
  background: var(--bg-surface); border: 1px solid var(--border);
  border-radius: 8px; padding: 16px; display: none;
  max-height: 80vh; overflow-y: auto; z-index: 10;
  box-shadow: 0 8px 24px rgba(0,0,0,0.4);
}}
#detail-panel h3 {{ color: var(--border-focus); margin-bottom: 8px; font-size: 14px; }}
#detail-panel .detail-row {{ margin-bottom: 6px; font-size: 12px; }}
#detail-panel .detail-label {{ color: var(--text-secondary); display: inline-block; width: 80px; }}
#detail-panel .detail-value {{ color: var(--text-primary); }}
#detail-panel .section-title {{
  color: #f0883e; font-size: 12px; font-weight: 600;
  margin-top: 12px; margin-bottom: 6px;
  border-top: 1px solid var(--border); padding-top: 8px;
}}
#detail-panel .dep-item {{ font-size: 11px; color: var(--text-primary); padding: 2px 0; cursor: pointer; }}
#detail-panel .dep-item:hover {{ color: var(--border-focus); }}
#close-detail {{
  position: absolute; top: 8px; right: 12px;
  background: none; border: none; color: var(--text-secondary);
  cursor: pointer; font-size: 18px;
}}

/* Legend */
.legend {{
  position: absolute; bottom: 16px; left: 50%; transform: translateX(-50%);
  background: var(--bg-surface); border: 1px solid var(--border);
  border-radius: 8px; padding: 8px 14px;
  display: flex; gap: 14px; font-size: 11px; z-index: 5;
}}
.legend-group {{ display: flex; align-items: center; gap: 8px; }}
.legend-group-title {{
  font-size: 11px; color: var(--text-muted);
  text-transform: uppercase; font-weight: 600;
}}
.legend-item {{ display: flex; align-items: center; gap: 4px; color: var(--text-secondary); }}
.legend-dot {{ width: 8px; height: 8px; border-radius: 50%; }}
.legend-line {{ width: 16px; height: 2px; border-radius: 1px; }}
.legend-line.dashed {{
  background: repeating-linear-gradient(90deg, var(--text-muted) 0 4px, transparent 4px 7px);
}}

/* CM-S1-07: Toolbar */
#toolbar {{
  position: absolute; bottom: 12px; left: 12px; z-index: 15;
  display: flex; gap: 4px; align-items: center;
}}
#toolbar .divider {{
  width: 1px; height: 24px; background: var(--border); margin: 0 4px;
}}
.tool-btn {{
  width: 36px; height: 36px; background: var(--bg-surface);
  border: 1px solid var(--border); border-radius: 8px;
  display: inline-flex; align-items: center; justify-content: center;
  color: var(--text-secondary); cursor: pointer; font-size: 14px;
}}
.tool-btn:hover {{ background: var(--bg-elevated); color: var(--text-primary); }}
.tool-btn.active {{ background: var(--hc-primary); border-color: var(--hc-primary); color: #fff; }}

/* CM-S1-06: Minimap */
#minimap {{
  position: absolute; bottom: 12px; right: 12px; z-index: 15;
  width: 180px; height: 120px; background: var(--bg-surface);
  border: 1px solid var(--border); border-radius: 8px;
  overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,.3);
  cursor: pointer;
}}
#minimap svg {{ width: 100%; height: 100%; background: var(--bg-canvas); }}
.minimap-viewport {{
  fill: rgba(99,102,241,.08); stroke: var(--hc-primary);
  stroke-width: 1.5; cursor: move;
}}
.minimap-cluster {{ fill-opacity: 0.15; stroke: none; }}
.minimap-node {{ fill-opacity: 0.6; stroke: none; }}

/* CM-S1-02: Domain cluster backgrounds */
.cluster-bg {{ fill-opacity: 0.04; stroke-opacity: 0.15; stroke-width: 1; pointer-events: none; }}
.cluster-label {{ font-size: 14px; font-weight: 700; fill-opacity: 0.3; pointer-events: none; }}

/* Graph */
svg {{ width: 100%; height: 100%; }}
.link {{ stroke-opacity: 0.3; }}
.link.highlighted {{ stroke-opacity: 0.8; stroke-width: 2px; }}
.node-circle {{ stroke-width: 1.5px; cursor: pointer; }}
.node-circle:hover {{ stroke-width: 3px; }}
.node-label {{ font-size: 11px; fill: var(--text-secondary); pointer-events: none; }}
.node-label.highlighted {{ fill: var(--text-primary); font-weight: 600; }}
</style>
</head>
<body>
<!-- HC-AI | ticket: FDD-TOOL-CODEMAP -->
<div id="app">
  <!-- CM-S1-10: Top bar -->
  <div id="topbar">
    <div class="logo-icon">CM</div>
    <span class="logo-text">Codebase Map</span>
    <span class="logo-ver">v1.1</span>
    <span class="stat-badge" id="stat-nodes"></span>
    <span class="stat-badge" id="stat-edges"></span>
    <span class="stat-badge" id="stat-domains"></span>
    <span class="timestamp" id="timestamp"></span>
  </div>

  <div id="main">
    <!-- CM-S1-01: Sidebar with domain tree -->
    <div id="sidebar">
      <div class="sidebar-search">
        <input type="text" id="search-box" placeholder="Search functions, classes...">
      </div>
      <div class="filters" id="filters"></div>
      <div id="search-result-count"></div>
      <div id="domain-tree"></div>
    </div>

    <div id="graph-container">
      <svg id="svg"></svg>
      <div id="detail-panel">
        <button id="close-detail">&times;</button>
        <div id="detail-content"></div>
      </div>
      <!-- CM-S1-07: Toolbar -->
      <div id="toolbar">
        <button class="tool-btn" id="btn-zoom-in" title="Zoom In">+</button>
        <button class="tool-btn" id="btn-zoom-out" title="Zoom Out">&minus;</button>
        <button class="tool-btn" id="btn-fit" title="Fit to Screen">&#9634;</button>
        <div class="divider"></div>
        <button class="tool-btn" id="btn-labels" title="Toggle Labels">T</button>
        <button class="tool-btn active" id="btn-edges" title="Toggle Edges">&#8596;</button>
        <button class="tool-btn active" id="btn-clusters" title="Toggle Clusters">&#9638;</button>
        <div class="divider"></div>
        <button class="tool-btn" id="btn-export" title="Export PNG">&#128247;</button>
        <button class="tool-btn" id="btn-fullscreen" title="Fullscreen">&#9974;</button>
      </div>
      <!-- CM-S1-08: Dual legend -->
      <div class="legend" id="legend"></div>
      <!-- CM-S1-06: Minimap -->
      <div id="minimap"><svg id="minimap-svg"></svg></div>
    </div>
  </div>
</div>

{d3_script}
<script>
// HC-AI | ticket: FDD-TOOL-CODEMAP
const DATA = {graph_json};

const LAYER_COLORS = {{
  route: '#f0883e', service: '#3fb950', repository: '#a371f7',
  model: '#f778ba', core: '#79c0ff', worker: '#d29922',
  router: '#f0883e', schema: '#f0883e', util: '#8b949e',
  test: '#6b7280', unknown: '#484f58'
}};
const TYPE_COLORS = {{
  route: '#f0883e', function: '#79c0ff', method: '#3fb950',
  class: '#a371f7', model: '#f778ba', celery_task: '#d29922'
}};
const TYPE_ICONS = {{
  class: '\\u25C6', route: '\\u25CF', method: '\\u0192',
  function: '\\u0192', model: '\\u25C6', celery_task: '\\u25CF'
}};
const DOMAIN_COLORS = {{
  crm: '#3fb950', cdp: '#a371f7', ecommerce: '#f0883e',
  private_traffic: '#58a6ff', core: '#79c0ff', auth: '#d29922',
  billing: '#f778ba'
}};

const nodes = DATA.nodes.map(n => ({{ ...n, id: n.id }}));
const edges = DATA.edges.filter(e =>
  nodes.some(n => n.id === e.source) && nodes.some(n => n.id === e.target)
).map(e => ({{ source: e.source, target: e.target, type: e.type }}));

// CM-S1-10: Top bar stats
const domainCount = DATA.stats.by_domain ? Object.keys(DATA.stats.by_domain).length : 0;
document.getElementById('stat-nodes').innerHTML = `<strong>${{nodes.length.toLocaleString()}}</strong> nodes`;
document.getElementById('stat-edges').innerHTML = `<strong>${{edges.length.toLocaleString()}}</strong> edges`;
document.getElementById('stat-domains').innerHTML = `<strong>${{domainCount}}</strong> domains`;
document.getElementById('timestamp').textContent = `Generated: ${{DATA.generated_at || new Date().toLocaleString()}}`;

// CM-S1-01: Layer filter chips
const filterContainer = document.getElementById('filters');
const layers = [...new Set(nodes.map(n => n.layer))].sort();
let activeFilters = new Set(layers);

layers.forEach(layer => {{
  const chip = document.createElement('button');
  chip.className = 'chip active';
  const dotColor = LAYER_COLORS[layer] || '#484f58';
  const count = nodes.filter(n => n.layer === layer).length;
  chip.innerHTML = `<span class="dot" style="background:${{dotColor}}"></span>${{layer}} <span class="count">${{count}}</span>`;
  chip.onclick = () => {{
    chip.classList.toggle('active');
    if (activeFilters.has(layer)) activeFilters.delete(layer);
    else activeFilters.add(layer);
    updateVisibility();
  }};
  filterContainer.appendChild(chip);
}});

// CM-S1-01: Build domain tree data
function buildDomainTree() {{
  const tree = {{}};
  nodes.forEach(n => {{
    if (!tree[n.domain]) tree[n.domain] = {{ classes: {{}}, standalone: [] }};
    if (n.type === 'class' || n.type === 'model') {{
      if (!tree[n.domain].classes[n.id]) {{
        tree[n.domain].classes[n.id] = {{ node: n, methods: [] }};
      }}
    }} else if (n.parent_class) {{
      const parentId = nodes.find(p => p.name === n.parent_class && p.domain === n.domain);
      const pid = parentId ? parentId.id : n.parent_class;
      if (!tree[n.domain].classes[pid]) {{
        tree[n.domain].classes[pid] = {{ node: parentId || null, methods: [] }};
      }}
      tree[n.domain].classes[pid].methods.push(n);
    }} else {{
      tree[n.domain].standalone.push(n);
    }}
  }});
  return tree;
}}

// CM-S1-01: Render domain tree
const domainTreeEl = document.getElementById('domain-tree');
const searchBox = document.getElementById('search-box');
const searchCountEl = document.getElementById('search-result-count');

function renderDomainTree(filter = '') {{
  const tree = buildDomainTree();
  const lowerFilter = filter.toLowerCase();

  // Sort domains by node count descending
  const domainStats = DATA.stats.by_domain || {{}};
  const sortedDomains = Object.keys(tree).sort((a, b) =>
    (domainStats[b] || 0) - (domainStats[a] || 0)
  );

  let totalVisible = 0;
  let html = '';

  sortedDomains.forEach(domain => {{
    const data = tree[domain];
    const domainColor = DOMAIN_COLORS[domain] || '#484f58';
    const allInDomain = [];

    // Collect all nodes in domain for filtering
    Object.values(data.classes).forEach(cls => {{
      if (cls.node) allInDomain.push(cls.node);
      cls.methods.forEach(m => allInDomain.push(m));
    }});
    data.standalone.forEach(n => allInDomain.push(n));

    // Filter by active layers + search
    const visible = allInDomain.filter(n =>
      activeFilters.has(n.layer) &&
      (lowerFilter === '' ||
       n.name.toLowerCase().includes(lowerFilter) ||
       n.id.toLowerCase().includes(lowerFilter))
    );

    if (visible.length === 0 && lowerFilter !== '') return;
    totalVisible += visible.length;
    const domainNodeCount = visible.length || allInDomain.filter(n => activeFilters.has(n.layer)).length;
    const isSearchActive = lowerFilter !== '';

    html += `<div class="domain-group">`;
    html += `<div class="domain-header" data-domain="${{domain}}">`;
    html += `<span class="arrow${{isSearchActive ? ' open' : ''}}">&#9654;</span>`;
    html += `<span class="domain-dot" style="background:${{domainColor}}"></span>`;
    html += `${{domain}}`;
    html += `<span class="domain-count">${{domainNodeCount}}</span>`;
    html += `</div>`;
    html += `<div class="domain-children${{isSearchActive ? ' open' : ''}}">`;

    // Classes with methods
    const visibleClassIds = new Set(visible.map(n => n.id));
    const visibleParents = new Set(visible.filter(n => n.parent_class).map(n => {{
      const p = nodes.find(pp => pp.name === n.parent_class && pp.domain === domain);
      return p ? p.id : n.parent_class;
    }}));

    Object.entries(data.classes).forEach(([cid, cls]) => {{
      if (!cls.node) return;
      const cn = cls.node;
      if (!activeFilters.has(cn.layer)) return;
      const classMatchesSearch = lowerFilter === '' ||
        cn.name.toLowerCase().includes(lowerFilter) ||
        cn.id.toLowerCase().includes(lowerFilter);
      const hasMatchingMethods = cls.methods.some(m =>
        activeFilters.has(m.layer) &&
        (m.name.toLowerCase().includes(lowerFilter) || m.id.toLowerCase().includes(lowerFilter))
      );
      if (lowerFilter !== '' && !classMatchesSearch && !hasMatchingMethods) return;

      const icon = TYPE_ICONS[cn.type] || '\\u0192';
      const iconColor = TYPE_COLORS[cn.type] || '#484f58';
      html += `<div class="node-item" data-id="${{cn.id}}" onclick="selectNodeById('${{cn.id}}')">`;
      html += `<span class="type-icon" style="color:${{iconColor}}">${{icon}}</span>`;
      html += `<span class="node-name">${{cn.name}}</span>`;
      html += `<span class="node-layer">${{cn.layer}}</span>`;
      html += `</div>`;

      if (cls.methods.length > 0) {{
        const methodsOpen = isSearchActive && hasMatchingMethods;
        html += `<div class="class-children${{methodsOpen ? ' open' : ''}}" data-class="${{cn.id}}">`;
        cls.methods.forEach(m => {{
          if (!activeFilters.has(m.layer)) return;
          if (lowerFilter !== '' && !m.name.toLowerCase().includes(lowerFilter) && !m.id.toLowerCase().includes(lowerFilter)) return;
          html += `<div class="method-item" data-id="${{m.id}}" onclick="selectNodeById('${{m.id}}')">&#8627; ${{m.name}}</div>`;
        }});
        html += `</div>`;
      }}
    }});

    // Standalone functions/routes
    data.standalone.forEach(n => {{
      if (!activeFilters.has(n.layer)) return;
      if (lowerFilter !== '' && !n.name.toLowerCase().includes(lowerFilter) && !n.id.toLowerCase().includes(lowerFilter)) return;
      const icon = TYPE_ICONS[n.type] || '\\u0192';
      const iconColor = TYPE_COLORS[n.type] || '#484f58';
      html += `<div class="node-item" data-id="${{n.id}}" onclick="selectNodeById('${{n.id}}')">`;
      html += `<span class="type-icon" style="color:${{iconColor}}">${{icon}}</span>`;
      html += `<span class="node-name">${{n.name}}</span>`;
      html += `<span class="node-layer">${{n.layer}}</span>`;
      html += `</div>`;
    }});

    html += `</div></div>`;
  }});

  // CM-S1-09: Empty state
  if (lowerFilter !== '' && totalVisible === 0) {{
    html = `<div class="empty-state">
      <div class="es-icon">&#128269;</div>
      <div class="es-title">No results found</div>
      <div class="es-hint">Try searching by function name, class, or domain</div>
    </div>`;
    searchCountEl.style.display = 'none';
  }} else if (lowerFilter !== '') {{
    searchCountEl.textContent = `${{totalVisible}} results`;
    searchCountEl.style.display = 'block';
  }} else {{
    searchCountEl.style.display = 'none';
  }}

  domainTreeEl.innerHTML = html;

  // Attach domain toggle events
  domainTreeEl.querySelectorAll('.domain-header').forEach(hdr => {{
    hdr.addEventListener('click', () => {{
      const arrow = hdr.querySelector('.arrow');
      const children = hdr.nextElementSibling;
      if (children) {{
        arrow.classList.toggle('open');
        children.classList.toggle('open');
      }}
    }});
  }});

  // Attach class toggle events
  domainTreeEl.querySelectorAll('.node-item').forEach(item => {{
    item.addEventListener('click', (e) => {{
      const classChildren = item.nextElementSibling;
      if (classChildren && classChildren.classList.contains('class-children')) {{
        classChildren.classList.toggle('open');
      }}
    }});
  }});
}}

searchBox.addEventListener('input', () => {{
  renderDomainTree(searchBox.value);
  updateGraphVisibility();
}});

function updateGraphVisibility() {{
  nodeG.style('display', d => activeFilters.has(d.layer) ? null : 'none');
  link.style('display', d => activeFilters.has(d.source.layer) && activeFilters.has(d.target.layer) ? null : 'none');
}}

function updateVisibility() {{
  updateGraphVisibility();
  renderDomainTree(searchBox.value);
}}

// Legend — dual groups (CM-S1-08 prep)
const legendEl = document.getElementById('legend');
legendEl.innerHTML = `
  <div class="legend-group">
    <span class="legend-group-title">Type</span>
    <span class="legend-item"><span class="legend-dot" style="background:#f0883e"></span>Route</span>
    <span class="legend-item"><span class="legend-dot" style="background:#a371f7"></span>Class</span>
    <span class="legend-item"><span class="legend-dot" style="background:#3fb950"></span>Method</span>
    <span class="legend-item"><span class="legend-dot" style="background:#79c0ff"></span>Func</span>
    <span class="legend-item"><span class="legend-dot" style="background:#f778ba"></span>Model</span>
    <span class="legend-item"><span class="legend-dot" style="background:#d29922"></span>Task</span>
  </div>
  <div class="legend-group">
    <span class="legend-group-title">Edge</span>
    <span class="legend-item"><span class="legend-line" style="background:var(--text-muted)"></span>calls</span>
    <span class="legend-item"><span class="legend-line dashed"></span>imports</span>
    <span class="legend-item"><span class="legend-line" style="background:#a371f7;height:3px"></span>inherits</span>
  </div>
`;

// D3 Force Graph
const svg = d3.select('#svg');
const width = document.getElementById('graph-container').clientWidth;
const height = document.getElementById('graph-container').clientHeight;

const g = svg.append('g');

const zoom = d3.zoom().scaleExtent([0.1, 8]).on('zoom', (e) => g.attr('transform', e.transform));
svg.call(zoom);

// HC-AI | ticket: FDD-TOOL-CODEMAP
// CM-S1-02: Domain clustering — compute cluster centers
const domains = [...new Set(nodes.map(n => n.domain))];
const clusterCenters = {{}};
const cols = Math.ceil(Math.sqrt(domains.length));
domains.forEach((domain, i) => {{
  const col = i % cols;
  const row = Math.floor(i / cols);
  const spacing = Math.max(width, height) / (cols + 1);
  clusterCenters[domain] = {{
    x: (col + 1) * spacing,
    y: (row + 1) * spacing
  }};
}});

// CM-S1-02: Custom clustering force
function forceCluster(strength) {{
  let nodeData;
  function force(alpha) {{
    for (const d of nodeData) {{
      const center = clusterCenters[d.domain];
      if (!center) continue;
      d.vx += (center.x - d.x) * strength * alpha;
      d.vy += (center.y - d.y) * strength * alpha;
    }}
  }}
  force.initialize = (n) => {{ nodeData = n; }};
  return force;
}}

const simulation = d3.forceSimulation(nodes)
  .force('link', d3.forceLink(edges).id(d => d.id).distance(80).strength(0.3))
  .force('charge', d3.forceManyBody().strength(-120))
  .force('center', d3.forceCenter(width / 2, height / 2))
  .force('collision', d3.forceCollide().radius(20))
  .force('cluster', forceCluster(0.3));

// CM-S1-02: Cluster background rects — drawn first (behind links/nodes)
const clusterG = g.append('g').attr('class', 'clusters');
const clusterPadding = 40;

const clusterRects = clusterG.selectAll('g')
  .data(domains).join('g');

clusterRects.append('rect')
  .attr('class', 'cluster-bg')
  .attr('rx', 16).attr('ry', 16)
  .attr('fill', d => DOMAIN_COLORS[d] || '#484f58')
  .attr('stroke', d => DOMAIN_COLORS[d] || '#484f58');

clusterRects.append('text')
  .attr('class', 'cluster-label')
  .attr('fill', d => DOMAIN_COLORS[d] || '#484f58')
  .text(d => {{
    const count = nodes.filter(n => n.domain === d).length;
    return `${{d}} (${{count}})`;
  }});

function updateClusters() {{
  clusterRects.each(function(domain) {{
    const domainNodes = nodes.filter(n => n.domain === domain && n.x != null);
    if (domainNodes.length === 0) return;
    const xs = domainNodes.map(n => n.x);
    const ys = domainNodes.map(n => n.y);
    const x1 = Math.min(...xs) - clusterPadding;
    const y1 = Math.min(...ys) - clusterPadding;
    const x2 = Math.max(...xs) + clusterPadding;
    const y2 = Math.max(...ys) + clusterPadding;
    const sel = d3.select(this);
    sel.select('rect')
      .attr('x', x1).attr('y', y1)
      .attr('width', x2 - x1).attr('height', y2 - y1);
    sel.select('text')
      .attr('x', x1 + 12).attr('y', y1 + 22);
  }});
}}

// CM-S1-08: Edge styles match dual legend (calls=solid, imports=dashed, inherits=thick)
const link = g.append('g').selectAll('line')
  .data(edges).join('line')
  .attr('class', 'link')
  .attr('stroke', d => d.type === 'inherits' ? '#a371f7' : '#30363d')
  .attr('stroke-width', d => d.type === 'inherits' ? 2 : 1)
  .attr('stroke-dasharray', d => d.type === 'imports' ? '4 3' : null);

const nodeG = g.append('g').selectAll('g')
  .data(nodes).join('g')
  .call(d3.drag()
    .on('start', (e, d) => {{ if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }})
    .on('drag', (e, d) => {{ d.fx = e.x; d.fy = e.y; }})
    .on('end', (e, d) => {{ if (!e.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }})
  );

nodeG.append('circle')
  .attr('class', 'node-circle')
  .attr('r', d => d.type === 'class' || d.type === 'model' ? 8 : d.type === 'route' ? 7 : 5)
  .attr('fill', d => TYPE_COLORS[d.type] || '#484f58')
  .attr('stroke', d => LAYER_COLORS[d.layer] || '#484f58')
  .on('click', (e, d) => selectNode(d));

nodeG.append('text')
  .attr('class', 'node-label')
  .attr('dx', 12)
  .attr('dy', 4)
  .text(d => d.name);

simulation.on('tick', () => {{
  link
    .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
    .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
  nodeG.attr('transform', d => `translate(${{d.x}},${{d.y}})`);
  updateClusters();
}});

// Node selection & detail
let selectedNode = null;

window.selectNodeById = function(id) {{
  const node = nodes.find(n => n.id === id);
  if (node) selectNode(node);
}};

function selectNode(d) {{
  selectedNode = d;

  const connectedIds = new Set();
  connectedIds.add(d.id);
  edges.forEach(e => {{
    const sid = typeof e.source === 'object' ? e.source.id : e.source;
    const tid = typeof e.target === 'object' ? e.target.id : e.target;
    if (sid === d.id) connectedIds.add(tid);
    if (tid === d.id) connectedIds.add(sid);
  }});

  nodeG.select('circle').attr('opacity', n => connectedIds.has(n.id) ? 1 : 0.15);
  nodeG.select('text').classed('highlighted', n => connectedIds.has(n.id));

  // CM-S1-02: Dim unrelated clusters
  const connectedDomains = new Set();
  connectedIds.forEach(id => {{
    const n = nodes.find(nn => nn.id === id);
    if (n) connectedDomains.add(n.domain);
  }});
  clusterRects.attr('opacity', dm => connectedDomains.has(dm) ? 1 : 0.15);

  link.classed('highlighted', e => {{
    const sid = typeof e.source === 'object' ? e.source.id : e.source;
    const tid = typeof e.target === 'object' ? e.target.id : e.target;
    return sid === d.id || tid === d.id;
  }}).attr('stroke', e => {{
    const sid = typeof e.source === 'object' ? e.source.id : e.source;
    return sid === d.id ? '#3fb950' : '#f0883e';
  }}).attr('opacity', e => {{
    const sid = typeof e.source === 'object' ? e.source.id : e.source;
    const tid = typeof e.target === 'object' ? e.target.id : e.target;
    return (sid === d.id || tid === d.id) ? 1 : 0.1;
  }});

  const deps = edges.filter(e => {{ const sid = typeof e.source === 'object' ? e.source.id : e.source; return sid === d.id; }});
  const dependents = edges.filter(e => {{ const tid = typeof e.target === 'object' ? e.target.id : e.target; return tid === d.id; }});

  const panel = document.getElementById('detail-panel');
  const content = document.getElementById('detail-content');
  content.innerHTML = `
    <h3>${{d.name}}</h3>
    <div class="detail-row"><span class="detail-label">Type:</span><span class="detail-value" style="color:${{TYPE_COLORS[d.type]}}">${{d.type}}</span></div>
    <div class="detail-row"><span class="detail-label">Layer:</span><span class="detail-value">${{d.layer}}</span></div>
    <div class="detail-row"><span class="detail-label">Domain:</span><span class="detail-value">${{d.domain}}</span></div>
    <div class="detail-row"><span class="detail-label">File:</span><span class="detail-value">${{d.file}}:${{d.line_start}}</span></div>
    ${{d.parent_class ? `<div class="detail-row"><span class="detail-label">Class:</span><span class="detail-value">${{d.parent_class}}</span></div>` : ''}}
    ${{d.decorators && d.decorators.length ? `<div class="detail-row"><span class="detail-label">Deco:</span><span class="detail-value">${{d.decorators.join(', ')}}</span></div>` : ''}}
    ${{d.params && d.params.length ? `<div class="detail-row"><span class="detail-label">Params:</span><span class="detail-value">${{d.params.join(', ')}}</span></div>` : ''}}
    ${{d.return_type ? `<div class="detail-row"><span class="detail-label">Returns:</span><span class="detail-value">${{d.return_type}}</span></div>` : ''}}
    ${{d.docstring ? `<div class="detail-row"><span class="detail-label">Doc:</span><span class="detail-value">${{d.docstring.substring(0, 200)}}</span></div>` : ''}}
    <div class="section-title">Dependencies (${{deps.length}})</div>
    ${{deps.map(e => {{ const tid = typeof e.target === 'object' ? e.target.id : e.target; const tname = tid.split('.').pop(); return `<div class="dep-item" onclick="selectNodeById('${{tid}}')">${{e.type}} &#8594; ${{tname}}</div>`; }}).join('')}}
    <div class="section-title">Dependents (${{dependents.length}})</div>
    ${{dependents.map(e => {{ const sid = typeof e.source === 'object' ? e.source.id : e.source; const sname = sid.split('.').pop(); return `<div class="dep-item" onclick="selectNodeById('${{sid}}')">${{e.type}} &#8592; ${{sname}}</div>`; }}).join('')}}
  `;
  panel.style.display = 'block';

  // Highlight in sidebar
  domainTreeEl.querySelectorAll('.node-item, .method-item').forEach(el => {{
    el.classList.remove('selected');
  }});
  const item = domainTreeEl.querySelector(`[data-id="${{d.id}}"]`);
  if (item) {{
    item.classList.add('selected');
    item.scrollIntoView({{ block: 'nearest' }});
    // Auto-expand parent domain + class
    const domainGroup = item.closest('.domain-children');
    if (domainGroup && !domainGroup.classList.contains('open')) {{
      domainGroup.classList.add('open');
      const arrow = domainGroup.previousElementSibling?.querySelector('.arrow');
      if (arrow) arrow.classList.add('open');
    }}
    const classGroup = item.closest('.class-children');
    if (classGroup && !classGroup.classList.contains('open')) {{
      classGroup.classList.add('open');
    }}
  }}
}}

document.getElementById('close-detail').onclick = () => {{
  document.getElementById('detail-panel').style.display = 'none';
  nodeG.select('circle').attr('opacity', 1);
  nodeG.select('text').classed('highlighted', false);
  link.classed('highlighted', false).attr('stroke', '#30363d').attr('opacity', 1);
  clusterRects.attr('opacity', 1);
  selectedNode = null;
  domainTreeEl.querySelectorAll('.node-item, .method-item').forEach(el => el.classList.remove('selected'));
}};

// Double-click to zoom to node
nodeG.on('dblclick', (e, d) => {{
  e.stopPropagation();
  svg.transition().duration(500).call(
    zoom.transform,
    d3.zoomIdentity.translate(width / 2, height / 2).scale(2).translate(-d.x, -d.y)
  );
}});

// Initial render
renderDomainTree();

// HC-AI | ticket: FDD-TOOL-CODEMAP
// CM-S1-07: Toolbar functionality
let showLabels = false;
let showEdges = true;
let showClusters = true;

function fitToScreen() {{
  const bounds = g.node().getBBox();
  if (bounds.width === 0 || bounds.height === 0) return;
  const fullWidth = bounds.width;
  const fullHeight = bounds.height;
  const midX = bounds.x + fullWidth / 2;
  const midY = bounds.y + fullHeight / 2;
  const scale = 0.8 / Math.max(fullWidth / width, fullHeight / height);
  const tx = width / 2 - scale * midX;
  const ty = height / 2 - scale * midY;
  svg.transition().duration(750).call(
    zoom.transform,
    d3.zoomIdentity.translate(tx, ty).scale(scale)
  );
}}

document.getElementById('btn-zoom-in').onclick = () => {{
  svg.transition().duration(300).call(zoom.scaleBy, 1.5);
}};
document.getElementById('btn-zoom-out').onclick = () => {{
  svg.transition().duration(300).call(zoom.scaleBy, 0.67);
}};
document.getElementById('btn-fit').onclick = fitToScreen;

document.getElementById('btn-labels').onclick = function() {{
  showLabels = !showLabels;
  this.classList.toggle('active', showLabels);
  nodeG.selectAll('.node-label').style('display', showLabels ? null : 'none');
}};
document.getElementById('btn-edges').onclick = function() {{
  showEdges = !showEdges;
  this.classList.toggle('active', showEdges);
  link.style('display', showEdges ? null : 'none');
}};
document.getElementById('btn-clusters').onclick = function() {{
  showClusters = !showClusters;
  this.classList.toggle('active', showClusters);
  clusterG.style('display', showClusters ? null : 'none');
}};

document.getElementById('btn-export').onclick = () => {{
  const svgEl = document.getElementById('svg');
  const serializer = new XMLSerializer();
  const svgStr = serializer.serializeToString(svgEl);
  const canvas = document.createElement('canvas');
  canvas.width = width * 2;
  canvas.height = height * 2;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#0d1117';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  const img = new Image();
  img.onload = () => {{
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    const a = document.createElement('a');
    a.download = 'codebase-map.png';
    a.href = canvas.toDataURL('image/png');
    a.click();
  }};
  img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svgStr);
}};

document.getElementById('btn-fullscreen').onclick = () => {{
  const el = document.getElementById('graph-container');
  if (!document.fullscreenElement) {{
    el.requestFullscreen().catch(() => {{}});
  }} else {{
    document.exitFullscreen();
  }}
}};

// Labels hidden by default
nodeG.selectAll('.node-label').style('display', 'none');

// HC-AI | ticket: FDD-TOOL-CODEMAP
// CM-S1-06: Minimap — overview + viewport indicator
const minimapSvg = d3.select('#minimap-svg');
const mmWidth = 180;
const mmHeight = 120;
let currentTransform = d3.zoomIdentity;

// Track zoom transform
const originalZoomHandler = zoom.on('zoom');
zoom.on('zoom', (e) => {{
  g.attr('transform', e.transform);
  currentTransform = e.transform;
  updateMinimapViewport();
}});

function updateMinimap() {{
  minimapSvg.selectAll('*').remove();
  const bounds = g.node().getBBox();
  if (bounds.width === 0) return;
  const pad = 40;
  const vbX = bounds.x - pad;
  const vbY = bounds.y - pad;
  const vbW = bounds.width + pad * 2;
  const vbH = bounds.height + pad * 2;
  minimapSvg.attr('viewBox', `${{vbX}} ${{vbY}} ${{vbW}} ${{vbH}}`);

  // Draw cluster backgrounds on minimap
  const domainBounds = {{}};
  nodes.forEach(n => {{
    if (n.x == null) return;
    if (!domainBounds[n.domain]) {{
      domainBounds[n.domain] = {{ x1: n.x, y1: n.y, x2: n.x, y2: n.y }};
    }} else {{
      const b = domainBounds[n.domain];
      b.x1 = Math.min(b.x1, n.x);
      b.y1 = Math.min(b.y1, n.y);
      b.x2 = Math.max(b.x2, n.x);
      b.y2 = Math.max(b.y2, n.y);
    }}
  }});
  Object.entries(domainBounds).forEach(([domain, b]) => {{
    const color = DOMAIN_COLORS[domain] || '#484f58';
    minimapSvg.append('rect')
      .attr('class', 'minimap-cluster')
      .attr('x', b.x1 - 20).attr('y', b.y1 - 20)
      .attr('width', b.x2 - b.x1 + 40).attr('height', b.y2 - b.y1 + 40)
      .attr('rx', 4).attr('fill', color);
  }});

  // Draw nodes as small dots
  nodes.forEach(n => {{
    if (n.x == null) return;
    const color = TYPE_COLORS[n.type] || '#484f58';
    minimapSvg.append('circle')
      .attr('class', 'minimap-node')
      .attr('cx', n.x).attr('cy', n.y)
      .attr('r', vbW / 120)
      .attr('fill', color);
  }});

  // Viewport indicator rect
  minimapSvg.append('rect')
    .attr('class', 'minimap-viewport')
    .attr('id', 'mm-viewport');

  updateMinimapViewport();
}}

function updateMinimapViewport() {{
  const vp = minimapSvg.select('#mm-viewport');
  if (vp.empty()) return;
  const t = currentTransform;
  const vpX = -t.x / t.k;
  const vpY = -t.y / t.k;
  const vpW = width / t.k;
  const vpH = height / t.k;
  vp.attr('x', vpX).attr('y', vpY).attr('width', vpW).attr('height', vpH);
}}

// Minimap click to pan
document.getElementById('minimap').addEventListener('click', (e) => {{
  const mmEl = document.getElementById('minimap-svg');
  const rect = mmEl.getBoundingClientRect();
  const svgVB = mmEl.viewBox.baseVal;
  if (!svgVB || svgVB.width === 0) return;
  const clickX = svgVB.x + (e.clientX - rect.left) / rect.width * svgVB.width;
  const clickY = svgVB.y + (e.clientY - rect.top) / rect.height * svgVB.height;
  const t = currentTransform;
  const newX = width / 2 - clickX * t.k;
  const newY = height / 2 - clickY * t.k;
  svg.transition().duration(500).call(
    zoom.transform,
    d3.zoomIdentity.translate(newX, newY).scale(t.k)
  );
}});

// Update minimap after simulation settles
simulation.on('end', updateMinimap);

// Fit to screen after simulation settles
setTimeout(() => {{
  fitToScreen();
  setTimeout(updateMinimap, 800);
}}, 3000);
</script>
</body>
</html>"""
