// UtiliCare Supervisor Operations Controller

let activeSupTab = 'rag';
let pollingInterval = null;

document.addEventListener('DOMContentLoaded', () => {
  fetchPendingTickets();
  fetchLatestTelemetry();
  // Poll queue every 3 seconds for seamless multi-tab live demo
  pollingInterval = setInterval(() => {
    fetchPendingTickets();
    fetchLatestTelemetry();
  }, 3000);
});

async function fetchPendingTickets() {
  try {
    const res = await fetch('/api/tickets/pending');
    if (!res.ok) return;
    const data = await res.json();
    renderPendingQueue(data.pending_tickets || []);
    renderDispatchedHistory(data.dispatched_tickets || []);
  } catch (err) {
    console.error('Error fetching pending tickets:', err);
  }
}

async function fetchLatestTelemetry() {
  try {
    const res = await fetch('/api/telemetry/latest');
    if (!res.ok) return;
    const data = await res.json();
    if (data && data.classification_result) {
      renderTelemetryState(data);
    }
  } catch (err) {
    console.error('Error fetching telemetry:', err);
  }
}

function renderPendingQueue(tickets) {
  const container = document.getElementById('pending-tickets-container');
  const countBadge = document.getElementById('pending-count-badge');
  countBadge.textContent = `${tickets.length} Draft${tickets.length === 1 ? '' : 's'}`;

  if (tickets.length === 0) {
    container.innerHTML = `
      <div class="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 text-center text-xs text-slate-500">
        <svg class="w-8 h-8 mx-auto text-slate-600 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
        <p class="font-medium text-slate-400">Queue is currently clear.</p>
        <p class="mt-1 text-[11px]">When an urgent incident is reported via the Customer Portal, the draft will appear here for verification.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = tickets.map(t => {
    const draftId = t.draft_id;
    const category = t.category || 'service_request';
    const priority = (t.priority || 'HIGH').toUpperCase();
    const area = t.area_code || t.customer_area_code || 'KOLOLO';
    const summary = t.summary || 'Urgent utility incident reported';

    return `
      <div id="card-${escapeHtml(draftId)}" class="bg-amber-950/20 border border-amber-600/40 rounded-2xl p-4 shadow-lg space-y-3 animate-fadeIn">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-2">
            <span class="font-mono text-xs font-bold text-cyan-300">[${escapeHtml(draftId)}]</span>
            <span class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40">
              pending_approval
            </span>
          </div>
          <span class="text-[10px] font-mono text-slate-400">${escapeHtml(t.created_at ? t.created_at.slice(11, 19) + ' UTC' : 'Just now')}</span>
        </div>

        <div class="grid grid-cols-3 gap-2 text-[11px]">
          <div>
            <span class="text-slate-500 font-mono text-[9px]">CATEGORY</span>
            <p class="font-semibold text-slate-200 capitalize">${escapeHtml(category)}</p>
          </div>
          <div>
            <span class="text-slate-500 font-mono text-[9px]">PRIORITY</span>
            <p class="font-semibold text-amber-400">${escapeHtml(priority)}</p>
          </div>
          <div>
            <span class="text-slate-500 font-mono text-[9px]">AREA CODE</span>
            <p class="font-semibold text-slate-200 font-mono">${escapeHtml(area)}</p>
          </div>
        </div>

        <div>
          <span class="text-slate-500 font-mono text-[9px]">SUPERVISOR SUMMARY NOTES (EDITABLE)</span>
          <textarea id="summary-${escapeHtml(draftId)}" rows="2" class="w-full mt-1 bg-slate-950 border border-slate-700 rounded-lg p-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 resize-none">${escapeHtml(summary)}</textarea>
        </div>

        <div class="flex items-center justify-end space-x-2 pt-2 border-t border-slate-800">
          <button onclick="rejectDraftTicket('${escapeHtml(draftId)}')" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition">
            Reject / Hold
          </button>
          <button onclick="approveDraftTicket('${escapeHtml(draftId)}')" id="btn-approve-${escapeHtml(draftId)}" class="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs shadow-md shadow-emerald-900/40 transition flex items-center space-x-1.5">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
            <span>Approve & Dispatch</span>
          </button>
        </div>
      </div>
    `;
  }).join('');
}

function renderDispatchedHistory(dispatched) {
  const container = document.getElementById('dispatched-history-list');
  if (!dispatched || dispatched.length === 0) {
    container.innerHTML = '<p class="text-slate-500 italic text-[11px]">No dispatched tickets in this session.</p>';
    return;
  }

  container.innerHTML = dispatched.map(d => `
    <div class="bg-slate-950/80 border border-slate-800 rounded-xl p-2.5 flex items-center justify-between text-[11px]">
      <div>
        <div class="flex items-center space-x-2">
          <span class="font-mono text-emerald-400 font-bold">${escapeHtml(d.draft_id)}</span>
          <span class="text-[9px] font-mono px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">DISPATCHED</span>
          <span class="text-slate-400 font-mono">Ref: ${escapeHtml(d.dispatch_reference || 'DSP-00000')}</span>
        </div>
        <p class="text-slate-300 text-xs mt-0.5 truncate max-w-sm">${escapeHtml(d.operator_notes || d.summary || '')}</p>
      </div>
      <span class="text-slate-500 font-mono text-[10px]">${escapeHtml(d.dispatched_at ? d.dispatched_at.slice(11, 19) + ' UTC' : '')}</span>
    </div>
  `).join('');
}

async function approveDraftTicket(draftId) {
  const summaryEl = document.getElementById(`summary-${draftId}`);
  const notes = summaryEl ? summaryEl.value : '';
  const btn = document.getElementById(`btn-approve-${draftId}`);
  if (btn) {
    btn.disabled = true;
    btn.textContent = 'Authorizing...';
  }

  try {
    const res = await fetch('/api/tickets/approve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        draft_id: draftId,
        operator_notes: notes,
        operator_id: "SUPERVISOR-4104"
      })
    });

    if (!res.ok) throw new Error('Authorization call failed');
    fetchPendingTickets();

  } catch (err) {
    alert('Approval error: ' + err.message);
    if (btn) {
      btn.disabled = false;
      btn.textContent = 'Approve & Dispatch';
    }
  }
}

async function rejectDraftTicket(draftId) {
  try {
    await fetch('/api/tickets/reject', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        draft_id: draftId,
        operator_id: "SUPERVISOR-4104"
      })
    });
    fetchPendingTickets();
  } catch (err) {
    console.error(err);
  }
}

function renderTelemetryState(result) {
  const classification = result.classification_result || {};
  const category = classification.category || 'other';
  const confidence = classification.confidence || 'medium';
  const stopReason = result.stop_reason || 'goal_achieved_grounded_guidance';
  const iterationCount = result.iteration_count || 1;
  const toolResults = result.tool_results || [];

  // Animate Workflow Pipeline
  ['sense', 'plan', 'observe', 'stop'].forEach(step => {
    const el = document.getElementById(`sup-step-${step}`);
    if (el) {
      el.classList.remove('active');
      el.classList.add('completed');
    }
  });
  const actEl = document.getElementById('sup-step-act');
  if (actEl) {
    actEl.classList.remove('active');
    actEl.classList.add(toolResults.length > 0 ? 'completed' : 'active');
  }

  document.getElementById('sup-iteration-badge').textContent = `Iteration: ${iterationCount} / 3`;
  document.getElementById('sup-latency-badge').textContent = `${result.latency_ms || 45.2} ms`;

  // Category
  const catBadge = document.getElementById('sup-category-badge');
  catBadge.textContent = category.toUpperCase();
  catBadge.className = 'px-2 py-0.5 rounded-full font-semibold text-xs border ' + getCatBadgeStyle(category);

  // Confidence
  const confBadge = document.getElementById('sup-confidence-badge');
  confBadge.textContent = `Confidence: ${confidence.toUpperCase()}`;
  confBadge.className = 'px-2 py-0.5 rounded-full font-semibold text-xs border ' + getConfBadgeStyle(confidence);

  // Stop Reason
  const stopBadge = document.getElementById('sup-stop-reason-badge');
  stopBadge.textContent = stopReason;
  stopBadge.className = 'font-mono px-2 py-0.5 rounded text-xs border ' + getStopReasonStyle(stopReason);

  // RAG Sources
  renderSupRAGSources(result.grounding_status, result.retrieved_sources);

  // Tool History
  renderSupToolsHistory(result.tool_results, result.tool_calls_made);

  // Memory History
  renderSupMemory(result.memory_context);

  // Trace JSON
  document.getElementById('sup-trace-json-viewer').textContent = JSON.stringify(result, null, 2);
}

function renderSupRAGSources(status, sources) {
  const badge = document.getElementById('sup-rag-status-badge');
  badge.textContent = status ? status.toUpperCase() : 'UNKNOWN';
  badge.className = 'px-2 py-0.5 rounded font-mono font-semibold text-xs border ' + (status === 'grounded' ? 'bg-emerald-950 text-emerald-300 border-emerald-800' : 'bg-amber-950 text-amber-300 border-amber-800');

  const container = document.getElementById('sup-rag-sources-list');
  if (!sources || sources.length === 0) {
    container.innerHTML = '<p class="text-slate-500 italic">No grounding sources retrieved for this query.</p>';
    return;
  }

  container.innerHTML = sources.map((s, idx) => `
    <div class="bg-slate-950/80 border border-slate-800 rounded-xl p-2.5 space-y-1">
      <div class="flex items-center justify-between">
        <span class="font-mono text-cyan-400 font-semibold">[${escapeHtml(s.doc_id || `KB-${idx+1}`)}]</span>
        <span class="text-[10px] text-slate-500 font-mono">${escapeHtml(s.category || 'SOP')}</span>
      </div>
      <div class="text-slate-200 font-medium text-xs">${escapeHtml(s.title || 'Controlled Knowledge Document')}</div>
    </div>
  `).join('');
}

function renderSupToolsHistory(toolResults, toolCallsMade) {
  const container = document.getElementById('sup-tools-history-list');
  if (!toolResults || toolResults.length === 0) {
    container.innerHTML = '<p class="text-slate-500 italic">No tools executed for this request (Zero unauthorized actions).</p>';
    return;
  }

  container.innerHTML = toolResults.map((tr, idx) => {
    const isSuccess = tr.success !== false;
    const toolName = tr.tool_name || (toolCallsMade && toolCallsMade[idx] && toolCallsMade[idx].tool_name) || 'tool';
    return `
      <div class="bg-slate-950/80 border ${isSuccess ? 'border-slate-800' : 'border-red-900/60'} rounded-xl p-2.5 space-y-1 font-mono text-[11px]">
        <div class="flex items-center justify-between">
          <span class="font-bold text-cyan-300">${escapeHtml(toolName)}()</span>
          <span class="px-1.5 py-0.5 rounded ${isSuccess ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : 'bg-red-950 text-red-300 border border-red-800'}">
            ${isSuccess ? 'SUCCESS' : 'FAILED'}
          </span>
        </div>
        <div class="bg-slate-900/90 rounded p-2 text-slate-300 overflow-x-auto text-[10px]">
          ${escapeHtml(JSON.stringify(tr.result || tr, null, 2))}
        </div>
      </div>
    `;
  }).join('');
}

function renderSupMemory(memoryContext) {
  const container = document.getElementById('sup-memory-cases-list');
  if (!memoryContext || memoryContext.length === 0) {
    container.innerHTML = '<p class="text-slate-500 italic">No historical case lookups recorded.</p>';
    return;
  }

  container.innerHTML = memoryContext.map(c => `
    <div class="bg-slate-950/80 border border-slate-800 rounded-xl p-2.5 space-y-1 text-xs">
      <div class="flex items-center justify-between">
        <span class="font-mono text-cyan-400 font-semibold">${escapeHtml(c.draft_id || 'CASE-ID')}</span>
        <span class="text-[10px] text-slate-500 font-mono">${escapeHtml(c.area_code || '')} • ${escapeHtml(c.service_type || '')}</span>
      </div>
      <p class="text-slate-300 text-xs">${escapeHtml(c.summary || 'Prior incident record')}</p>
    </div>
  `).join('');
}

function switchSupTab(tab) {
  activeSupTab = tab;
  ['rag', 'tools', 'memory', 'trace'].forEach(t => {
    const btn = document.getElementById(`sup-tab-btn-${t}`);
    const content = document.getElementById(`sup-tab-content-${t}`);
    if (t === tab) {
      btn.className = 'py-3 px-3 font-semibold border-b-2 border-cyan-500 text-cyan-400 transition-colors';
      content.classList.remove('hidden');
    } else {
      btn.className = 'py-3 px-3 font-semibold border-b-2 border-transparent text-slate-400 hover:text-slate-200 transition-colors';
      content.classList.add('hidden');
    }
  });
}

function copySupTraceJSON() {
  const viewer = document.getElementById('sup-trace-json-viewer');
  navigator.clipboard.writeText(viewer.textContent).then(() => {
    alert('Telemetry JSON copied to clipboard!');
  });
}

function getCatBadgeStyle(category) {
  switch (category.toLowerCase()) {
    case 'outage': return 'bg-amber-950 text-amber-300 border-amber-700';
    case 'service_request': return 'bg-blue-950 text-blue-300 border-blue-700';
    case 'billing': return 'bg-emerald-950 text-emerald-300 border-emerald-700';
    default: return 'bg-slate-800 text-slate-300 border-slate-700';
  }
}

function getConfBadgeStyle(conf) {
  switch (conf.toLowerCase()) {
    case 'high': return 'bg-emerald-950 text-emerald-400 border-emerald-800';
    case 'medium': return 'bg-cyan-950 text-cyan-400 border-cyan-800';
    default: return 'bg-slate-800 text-slate-400 border-slate-700';
  }
}

function getStopReasonStyle(reason) {
  if (reason.includes('ticket_drafted')) return 'bg-amber-950 text-amber-300 border-amber-800';
  if (reason.includes('goal_achieved')) return 'bg-emerald-950 text-emerald-300 border-emerald-800';
  if (reason.includes('clarification')) return 'bg-purple-950 text-purple-300 border-purple-800';
  return 'bg-slate-800 text-slate-300 border-slate-700';
}

function escapeHtml(str) {
  if (typeof str !== 'string') return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
