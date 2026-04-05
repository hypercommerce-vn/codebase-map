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
    """Build the complete HTML visualization page."""
    # HC-AI | ticket: FDD-TOOL-CODEMAP
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
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0d1117; color: #c9d1d9; overflow: hidden; }}

#app {{ display: flex; height: 100vh; }}
#sidebar {{ width: 360px; background: #161b22; border-right: 1px solid #30363d; display: flex; flex-direction: column; overflow: hidden; }}
#graph-container {{ flex: 1; position: relative; }}

.sidebar-header {{ padding: 16px; border-bottom: 1px solid #30363d; }}
.sidebar-header h1 {{ font-size: 16px; color: #58a6ff; margin-bottom: 8px; }}
.sidebar-header .stats {{ font-size: 12px; color: #8b949e; }}

#search-box {{ width: 100%; padding: 8px 12px; background: #0d1117; border: 1px solid #30363d; border-radius: 6px; color: #c9d1d9; font-size: 13px; margin-top: 8px; }}
#search-box:focus {{ outline: none; border-color: #58a6ff; }}

.filters {{ padding: 12px 16px; border-bottom: 1px solid #30363d; display: flex; gap: 6px; flex-wrap: wrap; }}
.filter-btn {{ padding: 4px 10px; font-size: 11px; border-radius: 12px; border: 1px solid #30363d; background: transparent; color: #8b949e; cursor: pointer; }}
.filter-btn.active {{ background: #1f6feb; border-color: #1f6feb; color: #fff; }}

#node-list {{ flex: 1; overflow-y: auto; padding: 8px; }}
.node-item {{ padding: 8px 12px; border-radius: 6px; cursor: pointer; font-size: 12px; margin-bottom: 2px; }}
.node-item:hover {{ background: #1c2128; }}
.node-item.selected {{ background: #1f6feb33; border-left: 3px solid #1f6feb; }}
.node-item .name {{ font-weight: 600; color: #e6edf3; }}
.node-item .meta {{ color: #8b949e; font-size: 11px; margin-top: 2px; }}

#detail-panel {{ position: absolute; top: 16px; right: 16px; width: 380px; background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; display: none; max-height: 80vh; overflow-y: auto; z-index: 10; box-shadow: 0 8px 24px rgba(0,0,0,0.4); }}
#detail-panel h3 {{ color: #58a6ff; margin-bottom: 8px; font-size: 14px; }}
#detail-panel .detail-row {{ margin-bottom: 6px; font-size: 12px; }}
#detail-panel .detail-label {{ color: #8b949e; display: inline-block; width: 80px; }}
#detail-panel .detail-value {{ color: #e6edf3; }}
#detail-panel .section-title {{ color: #f0883e; font-size: 12px; font-weight: 600; margin-top: 12px; margin-bottom: 6px; border-top: 1px solid #30363d; padding-top: 8px; }}
#detail-panel .dep-item {{ font-size: 11px; color: #c9d1d9; padding: 2px 0; cursor: pointer; }}
#detail-panel .dep-item:hover {{ color: #58a6ff; }}
#close-detail {{ position: absolute; top: 8px; right: 12px; background: none; border: none; color: #8b949e; cursor: pointer; font-size: 18px; }}

.legend {{ position: absolute; bottom: 16px; left: 376px; background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 12px; font-size: 11px; z-index: 5; }}
.legend-item {{ display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }}
.legend-dot {{ width: 10px; height: 10px; border-radius: 50%; }}

svg {{ width: 100%; height: 100%; }}
.link {{ stroke-opacity: 0.3; }}
.link.highlighted {{ stroke-opacity: 0.8; stroke-width: 2px; }}
.node-circle {{ stroke-width: 1.5px; cursor: pointer; }}
.node-circle:hover {{ stroke-width: 3px; }}
.node-label {{ font-size: 10px; fill: #8b949e; pointer-events: none; }}
.node-label.highlighted {{ fill: #e6edf3; font-weight: 600; }}
</style>
</head>
<body>
<div id="app">
  <div id="sidebar">
    <div class="sidebar-header">
      <h1>Codebase Map</h1>
      <div class="stats" id="stats"></div>
      <input type="text" id="search-box" placeholder="Search functions, classes...">
    </div>
    <div class="filters" id="filters"></div>
    <div id="node-list"></div>
  </div>
  <div id="graph-container">
    <svg id="svg"></svg>
    <div id="detail-panel">
      <button id="close-detail">&times;</button>
      <div id="detail-content"></div>
    </div>
    <div class="legend" id="legend"></div>
  </div>
</div>

{d3_script}
<script>
const DATA = {graph_json};

const COLORS = {{
  route: '#f0883e', service: '#3fb950', repository: '#a371f7',
  model: '#f778ba', core: '#79c0ff', worker: '#d29922',
  router: '#f0883e', util: '#8b949e', unknown: '#484f58'
}};
const TYPE_COLORS = {{
  route: '#f0883e', function: '#79c0ff', method: '#3fb950',
  class: '#a371f7', model: '#f778ba', celery_task: '#d29922'
}};

const nodes = DATA.nodes.map(n => ({{ ...n, id: n.id }}));
const edges = DATA.edges.filter(e =>
  nodes.some(n => n.id === e.source) && nodes.some(n => n.id === e.target)
).map(e => ({{ source: e.source, target: e.target, type: e.type }}));

// Stats
document.getElementById('stats').textContent =
  `${{nodes.length}} nodes | ${{edges.length}} edges | ${{DATA.stats.by_domain ? Object.keys(DATA.stats.by_domain).length : 0}} domains`;

// Filters
const filterContainer = document.getElementById('filters');
const layers = [...new Set(nodes.map(n => n.layer))].sort();
let activeFilters = new Set(layers);

layers.forEach(layer => {{
  const btn = document.createElement('button');
  btn.className = 'filter-btn active';
  btn.textContent = layer;
  btn.onclick = () => {{
    btn.classList.toggle('active');
    if (activeFilters.has(layer)) activeFilters.delete(layer);
    else activeFilters.add(layer);
    updateVisibility();
  }};
  filterContainer.appendChild(btn);
}});

// Legend
const legendEl = document.getElementById('legend');
Object.entries(TYPE_COLORS).forEach(([type, color]) => {{
  const item = document.createElement('div');
  item.className = 'legend-item';
  item.innerHTML = `<div class="legend-dot" style="background:${{color}}"></div>${{type}}`;
  legendEl.appendChild(item);
}});

// D3 Force Graph
const svg = d3.select('#svg');
const width = document.getElementById('graph-container').clientWidth;
const height = document.getElementById('graph-container').clientHeight;

const g = svg.append('g');

const zoom = d3.zoom().scaleExtent([0.1, 8]).on('zoom', (e) => g.attr('transform', e.transform));
svg.call(zoom);

const simulation = d3.forceSimulation(nodes)
  .force('link', d3.forceLink(edges).id(d => d.id).distance(80).strength(0.3))
  .force('charge', d3.forceManyBody().strength(-120))
  .force('center', d3.forceCenter(width / 2, height / 2))
  .force('collision', d3.forceCollide().radius(20));

const link = g.append('g').selectAll('line')
  .data(edges).join('line')
  .attr('class', 'link')
  .attr('stroke', '#30363d')
  .attr('stroke-width', 1);

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
  .attr('stroke', d => COLORS[d.layer] || '#484f58')
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
}});

// Search
const searchBox = document.getElementById('search-box');
const nodeList = document.getElementById('node-list');

function renderNodeList(filter = '') {{
  const filtered = nodes.filter(n =>
    activeFilters.has(n.layer) &&
    (filter === '' || n.name.toLowerCase().includes(filter.toLowerCase()) || n.id.toLowerCase().includes(filter.toLowerCase()))
  ).sort((a, b) => a.name.localeCompare(b.name));

  nodeList.innerHTML = filtered.slice(0, 200).map(n =>
    `<div class="node-item" data-id="${{n.id}}" onclick="selectNodeById('${{n.id}}')">
      <div class="name" style="color:${{TYPE_COLORS[n.type] || '#c9d1d9'}}">${{n.name}}</div>
      <div class="meta">${{n.layer}} | ${{n.domain}} | ${{n.type}}</div>
    </div>`
  ).join('');
}}

searchBox.addEventListener('input', () => renderNodeList(searchBox.value));

function updateVisibility() {{
  nodeG.style('display', d => activeFilters.has(d.layer) ? null : 'none');
  link.style('display', d => activeFilters.has(d.source.layer) && activeFilters.has(d.target.layer) ? null : 'none');
  renderNodeList(searchBox.value);
}}

// Node selection & detail
let selectedNode = null;

window.selectNodeById = function(id) {{
  const node = nodes.find(n => n.id === id);
  if (node) selectNode(node);
}};

function selectNode(d) {{
  selectedNode = d;

  // Highlight connections
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

  // Show detail panel
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
    ${{deps.map(e => {{ const tid = typeof e.target === 'object' ? e.target.id : e.target; const tname = tid.split('.').pop(); return `<div class="dep-item" onclick="selectNodeById('${{tid}}')">${{e.type}} -> ${{tname}}</div>`; }}).join('')}}
    <div class="section-title">Dependents (${{dependents.length}})</div>
    ${{dependents.map(e => {{ const sid = typeof e.source === 'object' ? e.source.id : e.source; const sname = sid.split('.').pop(); return `<div class="dep-item" onclick="selectNodeById('${{sid}}')">${{e.type}} <- ${{sname}}</div>`; }}).join('')}}
  `;
  panel.style.display = 'block';

  // Highlight in sidebar
  document.querySelectorAll('.node-item').forEach(el => el.classList.remove('selected'));
  const item = document.querySelector(`.node-item[data-id="${{d.id}}"]`);
  if (item) {{ item.classList.add('selected'); item.scrollIntoView({{ block: 'nearest' }}); }}
}}

document.getElementById('close-detail').onclick = () => {{
  document.getElementById('detail-panel').style.display = 'none';
  nodeG.select('circle').attr('opacity', 1);
  nodeG.select('text').classed('highlighted', false);
  link.classed('highlighted', false).attr('stroke', '#30363d').attr('opacity', 1);
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
renderNodeList();

// Fit to screen after simulation settles
setTimeout(() => {{
  const bounds = g.node().getBBox();
  const fullWidth = bounds.width;
  const fullHeight = bounds.height;
  const midX = bounds.x + fullWidth / 2;
  const midY = bounds.y + fullHeight / 2;
  const scale = 0.8 / Math.max(fullWidth / width, fullHeight / height);
  const translate = [width / 2 - scale * midX, height / 2 - scale * midY];
  svg.transition().duration(750).call(
    zoom.transform,
    d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale)
  );
}}, 3000);
</script>
</body>
</html>"""
