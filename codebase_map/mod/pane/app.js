// HC-AI | ticket: VIBE-105
// Pane controller: status line polling, tab switching, Graph tab.
// Day 2 scope — status line + Graph summary rendering from /api/graph.
// Full D3 interactive view lands with Timeline integration on Day 3+.

const API = {
  status: '/api/status',
  graph: '/api/graph',
};

const POLL_MS = 5000;

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

// ═══ STATUS LINE ═══

async function fetchStatus() {
  try {
    const r = await fetch(API.status, { cache: 'no-store' });
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return await r.json();
  } catch (e) {
    console.warn('status fetch failed', e);
    return null;
  }
}

function labelCi(s) {
  return { pass: 'pass', fail: 'fail', running: 'running', unknown: '—' }[s] || s;
}

function labelSnapshot(s) {
  return { clean: 'clean', dirty: 'dirty', unknown: '—' }[s] || s;
}

function labelRisk(s) {
  return { low: '🟢 Low', medium: '🟡 Medium', high: '🔴 High', unknown: '⚪ —' }[s] || s;
}

function dotClass(s) {
  if (s === 'pass' || s === 'clean' || s === 'low') return 'ok';
  if (s === 'running' || s === 'dirty' || s === 'medium') return 'warn';
  if (s === 'fail' || s === 'high') return 'err';
  return '';
}

function renderStatus(data) {
  if (!data) return;
  const setText = (field, value) => {
    const el = $(`[data-field="${field}"]`);
    if (el) el.textContent = value ?? '—';
  };
  setText('sprint', data.sprint || '—');
  setText('branch', data.branch || '—');
  setText('ci_state', labelCi(data.ci_state));
  setText('snapshot_state', labelSnapshot(data.snapshot_state));
  setText('risk_level', labelRisk(data.risk_level));

  const prLink = $('#pr-link');
  if (data.pr_number) {
    prLink.textContent = '#' + data.pr_number;
    prLink.href = data.pr_url || '#';
  } else {
    prLink.textContent = '—';
    prLink.removeAttribute('href');
  }

  const ciDot = $('#ci-dot');
  if (ciDot) ciDot.className = 'dot ' + dotClass(data.ci_state);
  const riskDot = $('#risk-dot');
  if (riskDot) riskDot.className = 'dot ' + dotClass(data.risk_level);
}

async function pollStatus() {
  const data = await fetchStatus();
  renderStatus(data);
}

// ═══ TABS ═══

function activateTab(name) {
  $$('.tab').forEach((t) => t.classList.toggle('active', t.dataset.tab === name));
  $$('.pane').forEach((p) => p.classList.toggle('active', p.id === 'pane-' + name));
  if (name === 'graph') loadGraph();
}

function wireTabs() {
  $$('.tab').forEach((tab) => {
    tab.addEventListener('click', () => activateTab(tab.dataset.tab));
  });
}

// ═══ GRAPH TAB ═══

let graphLoaded = false;

async function loadGraph() {
  if (graphLoaded) return;
  const body = $('#graph-body');
  const meta = $('#graph-meta');
  try {
    const r = await fetch(API.graph, { cache: 'no-store' });
    if (r.status === 404) {
      renderGraphMissing(body, meta);
      return;
    }
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const data = await r.json();
    renderGraphSummary(data, body, meta);
    graphLoaded = true;
  } catch (e) {
    renderGraphError(body, meta, e);
  }
}

function renderGraphMissing(body, meta) {
  meta.textContent = 'chưa có graph.json';
  body.innerHTML = `
    <div class="placeholder">
      <div class="placeholder-icon">📊</div>
      <h3>Chưa có graph</h3>
      <p>Chạy <code style="font-family: var(--font-mono); background: var(--bg-muted); padding: 2px 6px; border-radius: 4px;">codebase-map generate</code> trong repo để sinh graph.json.</p>
      <p class="muted">Sau đó bấm tab Graph để xem lại.</p>
    </div>
  `;
  // Allow retry on next activation
  graphLoaded = false;
}

function renderGraphError(body, meta, err) {
  meta.textContent = 'lỗi tải';
  body.innerHTML = `
    <div class="error-box">
      <strong>Không tải được graph.</strong>
      <code>${String(err)}</code>
    </div>
  `;
  graphLoaded = false;
}

function countByField(items, field) {
  const map = {};
  items.forEach((n) => {
    const k = n[field] || 'other';
    map[k] = (map[k] || 0) + 1;
  });
  return map;
}

function renderGraphSummary(data, body, meta) {
  const nodes = data.nodes || [];
  const edges = data.edges || [];
  meta.textContent = `${nodes.length} nodes · ${edges.length} edges · ${data.project || 'project'}`;

  const byLayer = countByField(nodes, 'layer');
  const byType = countByField(nodes, 'type');

  const card = (label, value, sub) =>
    `<div class="summary-card"><div class="label">${label}</div><div class="value">${value}</div><div class="sub">${sub || ''}</div></div>`;

  const topNodes = nodes
    .slice()
    .sort((a, b) => (b.line_end - b.line_start) - (a.line_end - a.line_start))
    .slice(0, 25);

  const html = `
    <div class="graph-summary">
      ${card('Nodes', nodes.length, '')}
      ${card('Edges', edges.length, '')}
      ${card('Layers', Object.keys(byLayer).length,
        Object.entries(byLayer).map(([k, v]) => `${k}:${v}`).join(' · '))}
      ${card('Types', Object.keys(byType).length,
        Object.entries(byType).map(([k, v]) => `${k}:${v}`).join(' · '))}
    </div>
    <h3 style="font-size:13px;margin:16px 0 8px;color:var(--text-secondary);">
      Top 25 largest nodes (by line count)
    </h3>
    <div class="node-list">
      ${topNodes.map((n) => `
        <div class="node-row ${n.layer || 'other'}" data-id="${n.id}" title="${n.id}">
          <span class="node-name">${n.name}</span>
          <span class="node-file">${n.file}:${n.line_start}</span>
        </div>
      `).join('')}
    </div>
  `;
  body.innerHTML = html;

  // Click → ask parent to run /cbm-impact on that node (Day 3+ sendPrompt wiring).
  body.querySelectorAll('.node-row').forEach((row) => {
    row.addEventListener('click', () => {
      const id = row.dataset.id;
      if (window.parent && window.parent !== window) {
        try {
          window.parent.postMessage({ type: 'cbm-impact', node: id }, '*');
        } catch (_) {
          /* no-op */
        }
      }
      console.log('cbm node clicked', id);
    });
  });
}

// ═══ BOOT ═══

document.addEventListener('DOMContentLoaded', () => {
  wireTabs();
  pollStatus();
  loadGraph();
  setInterval(pollStatus, POLL_MS);
});
