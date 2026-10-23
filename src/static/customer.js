// UtiliCare Customer Portal Controller

const CUSTOMER_SCENARIOS = {
  ntinda_outage: "Hello, our power has been out since 8 AM here in Ntinda. Is this a planned maintenance or a transformer fault?",
  kololo_burst: "A water main pipe burst right in front of Plot 14 Kololo, clean water is flooding the road urgently!",
  high_bill: "Why is my water bill twice as high as usual this month? What should I check before submitting a formal dispute?",
  meter_leak: "There is continuous water dripping from the meter box outside my house in Nakasero."
};

document.addEventListener('DOMContentLoaded', () => {
  const textarea = document.getElementById('customer-inquiry-input');
  const count = document.getElementById('customer-char-count');
  if (textarea && count) {
    textarea.addEventListener('input', () => {
      count.textContent = `${textarea.value.length} characters`;
    });
  }
});

function loadScenario(key) {
  const text = CUSTOMER_SCENARIOS[key];
  if (!text) return;
  const input = document.getElementById('customer-inquiry-input');
  input.value = text;
  document.getElementById('customer-char-count').textContent = `${text.length} characters`;
  input.focus();
}

function clearCustomerInput() {
  const input = document.getElementById('customer-inquiry-input');
  input.value = '';
  document.getElementById('customer-char-count').textContent = '0 characters';
}

function resetCustomerChat() {
  const chat = document.getElementById('customer-chat-messages');
  chat.innerHTML = `
    <div class="flex items-start space-x-3">
      <div class="w-8 h-8 rounded-lg bg-cyan-600/30 border border-cyan-500/30 text-cyan-300 flex items-center justify-center flex-shrink-0 text-sm font-bold">
        UC
      </div>
      <div class="bg-slate-800/80 border border-slate-700/60 rounded-2xl rounded-tl-none p-4 max-w-[85%] text-xs text-slate-200 leading-relaxed shadow-sm">
        <p class="font-semibold text-white text-sm mb-1">Conversation Reset.</p>
        <p class="text-slate-300">
          How can we help you with your electricity or water service today?
        </p>
      </div>
    </div>
  `;
  clearCustomerInput();
}

async function submitCustomerInquiry(e) {
  e.preventDefault();
  const input = document.getElementById('customer-inquiry-input');
  const message = input.value.trim();
  if (!message) return;

  const sendBtn = document.getElementById('customer-send-btn');
  const sendText = document.getElementById('customer-send-text');
  const sendSpinner = document.getElementById('customer-send-spinner');

  // Lock UI while sending
  sendBtn.disabled = true;
  sendText.textContent = 'Sending...';
  sendSpinner.classList.remove('hidden');

  appendCustomerUserBubble(message);
  input.value = '';
  document.getElementById('customer-char-count').textContent = '0 characters';

  try {
    const res = await fetch('/api/triage', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: message,
        use_bounded: true,
        demo_mode: false
      })
    });

    const resText = await res.text();
    let data;
    try {
      data = JSON.parse(resText);
    } catch {
      throw new Error(`Server response error (${res.status})`);
    }

    if (!res.ok) {
      throw new Error(data.detail || `Server returned error (${res.status})`);
    }

    const result = data.result || data;
    const guidance = data.guidance || (result.trace && result.trace[0] && result.trace[0].parsed && result.trace[0].parsed.grounded_guidance) || "Your inquiry has been received.";
    const sources = result.retrieved_sources || [];

    // Check if ticket draft was generated
    let draftId = null;
    if (result.draft_ticket_info && result.draft_ticket_info.draft_id) {
      draftId = result.draft_ticket_info.draft_id;
    } else if (result.tool_results) {
      for (const tr of result.tool_results) {
        if (tr.tool_name === 'draft_ticket' && tr.result && tr.result.draft_id) {
          draftId = tr.result.draft_id;
          break;
        }
      }
    }

    appendCustomerAgentBubble(guidance, sources, draftId);

  } catch (err) {
    appendCustomerErrorBubble(err.message);
  } finally {
    sendBtn.disabled = false;
    sendText.textContent = 'Send Inquiry';
    sendSpinner.classList.add('hidden');
  }
}

function appendCustomerUserBubble(text) {
  const chat = document.getElementById('customer-chat-messages');
  const div = document.createElement('div');
  div.className = 'flex items-start justify-end space-x-3 animate-fadeIn';
  div.innerHTML = `
    <div class="bg-cyan-600 text-white rounded-2xl rounded-tr-none p-3.5 max-w-[80%] text-xs shadow-md leading-relaxed">
      ${escapeHtml(text)}
    </div>
    <div class="w-7 h-7 rounded-lg bg-slate-700 border border-slate-600 text-slate-300 flex items-center justify-center flex-shrink-0 text-xs font-semibold">
      You
    </div>
  `;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

function appendCustomerAgentBubble(guidance, sources = [], draftId = null) {
  const chat = document.getElementById('customer-chat-messages');
  const div = document.createElement('div');
  div.className = 'flex items-start space-x-3 animate-fadeIn';

  let ticketNoticeHtml = '';
  if (draftId) {
    ticketNoticeHtml = `
      <div class="mt-3 bg-amber-950/40 border border-amber-600/40 rounded-xl p-3 flex items-start space-x-2.5 text-amber-200">
        <svg class="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        <div>
          <span class="font-bold text-amber-300">Incident Draft Logged:</span>
          <span class="font-mono text-cyan-300 font-semibold">[${escapeHtml(draftId)}]</span>
          <p class="text-[11px] text-amber-200/80 mt-0.5">
            This request has been drafted and escalated to the Operations Supervisor for dispatch verification.
          </p>
        </div>
      </div>
    `;
  }

  let sourcesHtml = '';
  if (sources && sources.length > 0) {
    sourcesHtml = `
      <div class="mt-3 pt-2 border-t border-slate-700/60 flex flex-wrap gap-1.5 items-center">
        <span class="text-[10px] text-slate-400 font-medium">Standard Operating Procedures:</span>
        ${sources.map(s => `
          <span class="px-1.5 py-0.5 rounded bg-slate-900 text-cyan-300 border border-cyan-800/60 text-[10px] font-mono">
            ${escapeHtml(s.doc_id || s.title || 'KB')}
          </span>
        `).join('')}
      </div>
    `;
  }

  div.innerHTML = `
    <div class="w-8 h-8 rounded-lg bg-cyan-600/30 border border-cyan-500/30 text-cyan-300 flex items-center justify-center flex-shrink-0 text-sm font-bold">
      UC
    </div>
    <div class="bg-slate-800/90 border border-slate-700/60 rounded-2xl rounded-tl-none p-4 max-w-[85%] text-xs text-slate-200 leading-relaxed shadow-md">
      <div class="whitespace-pre-wrap">${escapeHtml(guidance)}</div>
      ${ticketNoticeHtml}
      ${sourcesHtml}
    </div>
  `;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

function appendCustomerErrorBubble(errorText) {
  const chat = document.getElementById('customer-chat-messages');
  const div = document.createElement('div');
  div.className = 'flex items-start space-x-3 animate-fadeIn';
  div.innerHTML = `
    <div class="w-8 h-8 rounded-lg bg-red-600/30 border border-red-500/30 text-red-400 flex items-center justify-center flex-shrink-0 text-sm font-bold">
      !
    </div>
    <div class="bg-red-950/40 border border-red-800/60 rounded-2xl rounded-tl-none p-3.5 max-w-[85%] text-xs text-red-200 leading-relaxed">
      <span class="font-bold text-red-300">Notice:</span> ${escapeHtml(errorText)}
    </div>
  `;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
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
