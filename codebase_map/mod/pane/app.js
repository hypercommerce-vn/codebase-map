// HC-AI | ticket: VIBE-105
// Pane controller: status line polling, tab switching, Graph tab.
// Day 2 scope — status line + Graph summary rendering from /api/graph.
// Full D3 interactive view lands with Timeline integration on Day 3+.

const API = {
  status: '/api/status',
  graph: '/api/graph',
  snapshots: '/api/snapshots',
  snapshot: (id) => `/api/snapshots/${encodeURIComponent(id)}`,
  diff: (id, base) =>
    `/api/snapshots/${encodeURIComponent(id)}/diff?base=${encodeURIComponent(base)}`,
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
  if (name === 'timeline') loadTimeline();
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

// ═══ TIMELINE TAB ═══

let timelineLoaded = false;
let timelineState = { snapshots: [], selected: null, base: null };

async function loadTimeline() {
  if (timelineLoaded) return;
  const body = $('#timeline-body');
  const meta = $('#timeline-meta');
  try {
    const r = await fetch(API.snapshots, { cache: 'no-store' });
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const data = await r.json();
    const snaps = data.snapshots || [];
    if (snaps.length === 0) {
      renderTimelineEmpty(body, meta, data.hint);
      return;
    }
    timelineState.snapshots = snaps;
    // Default: newest = selected, oldest = base.
    timelineState.selected = snaps[0].id;
    timelineState.base = snaps[snaps.length - 1].id;
    renderTimeline(body, meta);
    timelineLoaded = true;
  } catch (e) {
    renderTimelineError(body, meta, e);
  }
}

function renderTimelineEmpty(body, meta, hint) {
  meta.textContent = '0 snapshots';
  body.innerHTML = `
    <div class="placeholder">
      <div class="placeholder-icon">🕐</div>
      <h3>Chưa có snapshot</h3>
      <p>${hint || 'Chạy codebase-map generate để tạo snapshot đầu tiên.'}</p>
    </div>
  `;
  timelineLoaded = false;
}

function renderTimelineError(body, meta, err) {
  meta.textContent = 'lỗi tải';
  body.innerHTML = `
    <div class="error-box">
      <strong>Không tải được snapshots.</strong>
      <code>${String(err)}</code>
    </div>
  `;
  timelineLoaded = false;
}

function fmtDate(iso) {
  if (!iso) return '—';
  try {
    const d = new Date(iso);
    const pad = (n) => String(n).padStart(2, '0');
    return `${pad(d.getDate())}/${pad(d.getMonth() + 1)} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
  } catch (_) {
    return iso.slice(0, 16);
  }
}

function renderTimeline(body, meta) {
  const { snapshots, selected, base } = timelineState;
  meta.textContent = `${snapshots.length} snapshots · base=${shortId(base)} · head=${shortId(selected)}`;

  const rows = snapshots
    .map((s, i) => {
      const classes = ['timeline-row'];
      if (s.id === selected) classes.push('selected');
      if (s.id === base) classes.push('base');
      const sprintCls = i === 0 ? 'newest' : i === snapshots.length - 1 ? 'oldest' : '';
      return `
        <div class="${classes.join(' ')} ${sprintCls}" data-id="${s.id}">
          <div class="tl-dot"></div>
          <div class="tl-body">
            <div class="tl-head">
              <span class="tl-label">${escapeHtml(s.label || s.id)}</span>
              <span class="tl-meta">${fmtDate(s.generated_at)}</span>
            </div>
            <div class="tl-sub">
              <code>${escapeHtml(s.branch)}@${escapeHtml(s.commit_sha || '')}</code>
              · ${s.nodes}n · ${s.edges}e
            </div>
          </div>
          <div class="tl-actions">
            <button class="tl-btn" data-act="set-base" title="Dùng làm baseline">Base</button>
            <button class="tl-btn" data-act="set-head" title="Dùng làm head">Head</button>
          </div>
        </div>`;
    })
    .join('');

  body.innerHTML = `
    <div class="timeline-list">${rows}</div>
    <div class="timeline-diff" id="timeline-diff">
      <div class="placeholder" style="padding: 24px;">
        <p class="muted">Chọn Base + Head rồi bấm <strong>Compare</strong>.</p>
        <button class="tl-btn primary" id="tl-compare">Compare base → head</button>
      </div>
    </div>
  `;

  body.querySelectorAll('.timeline-row').forEach((row) => {
    row.addEventListener('click', (e) => {
      const act = e.target.dataset?.act;
      if (act === 'set-base') {
        timelineState.base = row.dataset.id;
      } else if (act === 'set-head') {
        timelineState.selected = row.dataset.id;
      } else {
        // Clicking the row body selects as head (most common action).
        timelineState.selected = row.dataset.id;
      }
      renderTimeline(body, meta);
    });
  });
  $('#tl-compare')?.addEventListener('click', loadDiff);
}

function shortId(id) {
  if (!id) return '—';
  // Strip the leading graph_ and trailing _<sha> noise for a readable tag.
  const m = id.match(/graph_(.+?)_(\d{8}_\d{4})?_?([a-f0-9]{7,})$/);
  if (m) return m[3].slice(0, 7);
  return id.slice(0, 12);
}

function escapeHtml(s) {
  if (s == null) return '';
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

async function loadDiff() {
  const { base, selected } = timelineState;
  const box = $('#timeline-diff');
  if (!base || !selected) {
    box.innerHTML = '<div class="error-box">Chưa chọn đủ Base + Head.</div>';
    return;
  }
  if (base === selected) {
    box.innerHTML = '<div class="placeholder"><p>Base và Head giống nhau — không có gì để diff.</p></div>';
    return;
  }
  box.innerHTML = '<div class="placeholder" style="padding:24px;"><div class="spinner"></div><p>Đang tính diff…</p></div>';
  try {
    const r = await fetch(API.diff(selected, base), { cache: 'no-store' });
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const data = await r.json();
    renderDiff(box, data);
  } catch (e) {
    box.innerHTML = `<div class="error-box"><strong>Diff thất bại.</strong><code>${String(e)}</code></div>`;
  }
}

function renderDiff(box, result) {
  const s = result.summary || {};
  const card = (label, value, cls) =>
    `<div class="summary-card ${cls || ''}"><div class="label">${label}</div><div class="value">${value}</div></div>`;

  const changes = (result.node_changes || []).slice(0, 10);
  const changesHtml = changes.length
    ? `<h3 style="font-size:13px;margin:16px 0 8px;color:var(--text-secondary);">
         First ${changes.length} node change${changes.length > 1 ? 's' : ''}
       </h3>
       <div class="node-list">
         ${changes
           .map((c) => {
             const n = c.node || {};
             const badge = `<span class="diff-badge ${c.change_type}">${c.change_type}</span>`;
             return `<div class="node-row ${n.layer || 'other'}">
               ${badge}
               <span class="node-name">${escapeHtml(n.name || n.id || '?')}</span>
               <span class="node-file">${escapeHtml(n.file || '')}:${n.line_start || ''}</span>
             </div>`;
           })
           .join('')}
       </div>`
    : '<p class="muted" style="padding:12px;">Không có thay đổi node nào.</p>';

  box.innerHTML = `
    <h3 style="font-size:13px;margin:4px 0 10px;color:var(--text-secondary);">Diff summary</h3>
    <div class="graph-summary">
      ${card('+ Added', s.functions_added || 0, 'add')}
      ${card('− Removed', s.functions_removed || 0, 'del')}
      ${card('Δ Modified', s.functions_modified || 0, 'mod')}
      ${card('⇄ Renamed', s.functions_renamed || 0)}
      ${card('+ Edges', s.edges_added || 0, 'add')}
      ${card('− Edges', s.edges_removed || 0, 'del')}
      ${card('⚠ Affected callers', s.affected_callers || 0, 'warn')}
    </div>
    ${changesHtml}
  `;
}

// ═══ BOOT ═══

document.addEventListener('DOMContentLoaded', () => {
  wireTabs();
  pollStatus();
  loadGraph();
  setInterval(pollStatus, POLL_MS);
});
