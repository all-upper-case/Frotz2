const input = document.getElementById('cmd-input');
const log = document.getElementById('log');
const hud = document.getElementById('hud');
const term = document.getElementById('terminal');

// Settings Elements
const themeSelect = document.getElementById('theme-select');
const fontSizeRange = document.getElementById('font-size-range');

// Matrix Elements
const matrixBtn = document.getElementById('matrix-btn');
const modal = document.getElementById('god-modal');
const modalClose = document.getElementById('god-close');
const godSave = document.getElementById('god-save');
const godBody = document.getElementById('god-tbody');

window.addEventListener('DOMContentLoaded', async () => {
    loadSettings();
    try {
        const res = await fetch('/get_state');
        const data = await res.json();

        if (data.response === "INITIALIZING_GENESIS") {
            appendLog("NO WORLD DATA FOUND.", 'system');
            appendLog("INITIATING GENESIS PROTOCOL...", 'system');
            triggerReset();
        } else {
            appendLog(data.response, 'system');
            if (data.state) updateHUD(data.state);
        }
    } catch(e) {
        appendLog("CONNECTION FAILED.", 'error');
    }
});

function loadSettings() {
    const s = JSON.parse(localStorage.getItem('zmachine_settings') || '{}');
    if (s.theme) {
        document.body.className = s.theme === 'clean' ? 'clean-theme' : '';
        themeSelect.value = s.theme;
    }
    if (s.fontSize) {
        document.documentElement.style.setProperty('--font-size', s.fontSize + 'px');
        fontSizeRange.value = s.fontSize;
    }
}

function saveSettings() {
    const s = {
        theme: themeSelect.value,
        fontSize: fontSizeRange.value
    };
    localStorage.setItem('zmachine_settings', JSON.stringify(s));
}

themeSelect.addEventListener('change', () => {
    document.body.className = themeSelect.value === 'clean' ? 'clean-theme' : '';
    saveSettings();
});

fontSizeRange.addEventListener('input', () => {
    document.documentElement.style.setProperty('--font-size', fontSizeRange.value + 'px');
    saveSettings();
});

// --- Game Logic ---

async function triggerReset() {
    appendLog("READING LORE... CONSTRUCTING MATTER... (PLEASE WAIT)", 'system');
    try {
        const res = await fetch('/reset', {method: 'POST'});
        const data = await res.json();

        log.innerHTML = ''; 
        appendLog(data.response || "World reset failed.", data.state ? 'system' : 'error');
        if (data.state) updateHUD(data.state);
    } catch(e) {
        appendLog("World reset failed.", 'error');
    }
}

document.getElementById('send-btn').onclick = sendCommand;
input.addEventListener('keydown', (e) => { if (e.key === 'Enter') sendCommand(); });

document.getElementById('hud-toggle').onclick = (e) => {
    e.stopPropagation();
    hud.classList.add('open');
};

document.getElementById('hud-close').onclick = () => hud.classList.remove('open');

// Tap outside HUD to close
hud.onclick = (e) => {
    if (e.target === hud) hud.classList.remove('open');
};

// --- Debug Logic ---
const debugBtn = document.getElementById('debug-btn');
const debugModal = document.getElementById('debug-modal');
const debugClose = document.getElementById('debug-close');
const debugContent = document.getElementById('debug-content');

debugBtn.onclick = async () => {
    debugModal.classList.remove('hidden');
    debugContent.textContent = "Fetching debug artifacts...";
    try {
        const res = await fetch('/get_debug');
        const data = await res.json();
        if (data.error) {
            debugContent.textContent = data.error;
            return;
        }
        if (!Array.isArray(data)) {
            debugContent.textContent = "Debug payload was not in the expected format.";
            return;
        }
        
        // Find the most recent turn
        const latest = data[data.length - 1];
        if (latest) {
            let output = "";
            const raw = latest.raw_response_from_llm || {};
            const usage = raw._usage || {};
            
            output += `=== SESSION METRICS ===\n`;
            output += `Input: ${usage.input_tokens || 0} | Output: ${usage.output_tokens || 0} | Total: ${usage.total_tokens || 0}\n\n`;
            
            if (raw.reasoning_content) {
                output += `=== AI REASONING ===\n${raw.reasoning_content}\n\n`;
            }
            
            output += `=== NARRATIVE ===\n${raw.narrative || "No narrative found."}\n\n`;
            
            if (raw.state_updates && raw.state_updates.length > 0) {
                output += `=== STATE UPDATES ===\n${JSON.stringify(raw.state_updates, null, 2)}\n\n`;
            }

            output += `=== RAW JSON ===\n${JSON.stringify(raw, null, 2)}`;
            debugContent.textContent = output;
        } else {
            debugContent.textContent = "No turn data available yet.";
        }
    } catch(e) {
        debugContent.textContent = "Error loading debug info.";
    }
};
debugClose.onclick = () => debugModal.classList.add('hidden');
debugModal.onclick = (e) => { if (e.target === debugModal) debugModal.classList.add('hidden'); };

async function sendCommand() {
    const text = input.value.trim();
    if (!text) return;

    if (text === '/reset') {
        if(confirm("Wipe world and regenerate from Lore?")) triggerReset();
        input.value = '';
        return;
    }

    if (text === '/models') {
        appendLog("> /models", 'user');
        input.value = '';
        try {
            const res = await fetch('/models');
            const data = await res.json();
            if (!Array.isArray(data) || data.length === 0) {
                appendLog("No Venice models are available. Check the API key and try again.", 'error');
                return;
            }
            let msg = "### AVAILABLE VENICE MODELS\n\n";
            data.forEach(m => {
                const reasoning = m.reasoning ? "Reasoning Support" : "";
                const pricePrompt = m.pricing && m.pricing.prompt ? (parseFloat(m.pricing.prompt) * 1000000).toFixed(2) : "?";
                const priceComp = m.pricing && m.pricing.completion ? (parseFloat(m.pricing.completion) * 1000000).toFixed(2) : "?";
                const contextWindow = Number.isFinite(m.context_window) ? m.context_window.toLocaleString() : m.context_window;
                
                msg += `- **${m.id}**\n  *${m.name}*\n  Context: ${contextWindow} tokens | ${reasoning}\n  Pricing: ${pricePrompt}/1M input, ${priceComp}/1M output\n\n`;
            });
            msg += "Type `/model [ID]` to switch.";
            appendLog(msg, 'system');
        } catch(e) { appendLog("Failed to fetch models.", 'error'); }
        return;
    }

    if (text.startsWith('/model ')) {
        const m = text.split(' ')[1];
        appendLog(`> /model ${m}`, 'user');
        input.value = '';
        try {
            const res = await fetch('/set_model', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({model: m})
            });
            const data = await res.json();
            if (data.status === 'success') {
                appendLog(`Model switched to **${m}**.`, 'system');
            } else {
                appendLog("Failed to switch model.", 'error');
            }
        } catch(e) { appendLog("Failed to switch model.", 'error'); }
        return;
    }

    appendLog(`> ${text}`, 'user');
    input.value = '';

    try {
        const res = await fetch('/command', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({input: text})
        });
        const data = await res.json();

        appendLog(data.response || "No response returned.", data.state ? 'ai' : 'error');
        if (data.state) updateHUD(data.state);
    } catch (e) {
        appendLog("Communication Error.", 'error');
    }
}

function appendLog(html, type) {
    const div = document.createElement('div');
    div.className = `msg ${type}`;
    div.innerHTML = marked.parse(html || "");
    log.appendChild(div);
    term.scrollTop = term.scrollHeight;
}

function updateHUD(state) {
    document.getElementById('stat-loc').textContent = state.location;
    document.getElementById('stat-exits').textContent = state.exits.join(', ').toUpperCase();
    document.getElementById('stat-tokens').textContent = `Total Session Tokens: ${state.total_tokens || 0}`;

    const ul = document.getElementById('stat-inv');
    ul.innerHTML = '';

    if (state.body && state.body.length > 0) {
        const hBody = document.createElement('li');
        hBody.innerHTML = '<strong style="color:var(--dim-color); font-size:0.85em;">[BODY]</strong>';
        ul.appendChild(hBody);
        state.body.forEach(i => {
            const li = document.createElement('li');
            li.textContent = i;
            ul.appendChild(li);
        });
        const spacer = document.createElement('li');
        spacer.style.height = '10px';
        ul.appendChild(spacer);
    }

    if (state.worn && state.worn.length > 0) {
        const hWorn = document.createElement('li');
        hWorn.innerHTML = '<strong style="color:var(--dim-color); font-size:0.85em;">[WORN]</strong>';
        ul.appendChild(hWorn);
        state.worn.forEach(i => {
            const li = document.createElement('li');
            li.textContent = i;
            ul.appendChild(li);
        });
        const spacer = document.createElement('li');
        spacer.style.height = '10px';
        ul.appendChild(spacer);
    }

    if (state.inventory && state.inventory.length > 0) {
        const hInv = document.createElement('li');
        hInv.innerHTML = '<strong style="color:var(--dim-color); font-size:0.85em;">[CARRIED]</strong>';
        ul.appendChild(hInv);
        state.inventory.forEach(i => {
            const li = document.createElement('li');
            li.textContent = i;
            ul.appendChild(li);
        });
    } else {
        const li = document.createElement('li');
        li.textContent = '(Empty)';
        li.style.color = '#555';
        ul.appendChild(li);
    }
}

// --- MATRIX LOGIC ---

matrixBtn.onclick = async () => {
    modal.classList.remove('hidden');
    godBody.innerHTML = '<tr><td colspan="4">Loading Reality...</td></tr>';

    try {
        const res = await fetch('/get_god_state');
        const data = await res.json();
        renderMatrix(data);
    } catch(e) {
        godBody.innerHTML = '<tr><td colspan="4">Could not load reality state.</td></tr>';
    }
};

modalClose.onclick = () => modal.classList.add('hidden');

function appendLabeledInput(container, labelText, className, value, multiline = false) {
    const wrapper = document.createElement('div');
    wrapper.style.marginTop = '5px';

    const label = document.createElement('strong');
    label.textContent = labelText;
    wrapper.appendChild(label);
    wrapper.appendChild(document.createTextNode(' '));

    const field = multiline ? document.createElement('textarea') : document.createElement('input');
    field.className = className;
    field.value = value || '';
    if (multiline) {
        field.style.width = '100%';
        field.style.height = '60px';
        field.style.background = '#222';
        field.style.color = '#0f0';
        field.style.border = '1px solid #444';
    } else {
        field.type = 'text';
    }

    wrapper.appendChild(field);
    container.appendChild(wrapper);
}

function renderMatrix(data) {
    godBody.innerHTML = '';
    const items = Array.isArray(data.items) ? data.items : [];
    const rooms = Array.isArray(data.rooms) ? data.rooms : [];

    if (items.length === 0) {
        godBody.innerHTML = '<tr><td colspan="4">No items found in the current world.</td></tr>';
        return;
    }

    items.forEach(item => {
        // Main Row
        const tr = document.createElement('tr');
        tr.dataset.id = item.id;
        tr.dataset.origAliases = item.aliases || '';
        tr.dataset.origDesc = item.description || '';

        const tdName = document.createElement('td');
        tdName.textContent = item.name || '(unnamed item)';
        tr.appendChild(tdName);

        const tdLoc = document.createElement('td');
        tdLoc.textContent = item.location || 'Unknown';
        tr.appendChild(tdLoc);

        const tdNew = document.createElement('td');
        const sel = document.createElement('select');
        ['(Unchanged)', 'Inventory', 'Worn', 'Void'].forEach(opt => {
            const o = document.createElement('option');
            o.value = opt; o.textContent = opt;
            sel.appendChild(o);
        });
        rooms.forEach(r => {
            const o = document.createElement('option');
            o.value = r.id; 
            o.textContent = `Room: ${r.name}`;
            sel.appendChild(o);
        });
        tdNew.appendChild(sel);
        tr.appendChild(tdNew);

        // Details Button
        const tdBtn = document.createElement('td');
        const btn = document.createElement('button');
        btn.textContent = "DETAILS";
        btn.style.fontSize = "0.8em";
        btn.onclick = () => {
            const nextRow = tr.nextElementSibling;
            nextRow.classList.toggle('hidden');
        };
        tdBtn.appendChild(btn);
        tr.appendChild(tdBtn);

        godBody.appendChild(tr);

        // Details Row
        const trDet = document.createElement('tr');
        trDet.className = "details-row hidden";
        trDet.dataset.parent = item.id;

        const tdDet = document.createElement('td');
        tdDet.colSpan = 4;

        const divDet = document.createElement('div');
        divDet.style.padding = "10px";
        divDet.style.background = "#080808";

        appendLabeledInput(divDet, 'Aliases:', 'edit-aliases', item.aliases || '');
        appendLabeledInput(divDet, 'Description:', 'edit-desc', item.description || '', true);
        appendLabeledInput(divDet, 'Auto-Fix (AI):', 'fix-prompt', '');

        tdDet.appendChild(divDet);
        trDet.appendChild(tdDet);
        godBody.appendChild(trDet);
    });
}

godSave.onclick = async () => {
    const changes = [];
    const rows = godBody.querySelectorAll('tr[data-id]');

    rows.forEach(row => {
        const id = row.dataset.id;
        const sel = row.querySelector('select');
        const nextRow = row.nextElementSibling;

        const aliasesInp = nextRow.querySelector('.edit-aliases');
        const descInp = nextRow.querySelector('.edit-desc');
        const fixInp = nextRow.querySelector('.fix-prompt');

        // Collect changes
        const change = { id: id };
        let hasChange = false;

        if (sel.value !== '(Unchanged)') {
            change.newLocation = sel.value;
            hasChange = true;
        }

        // Check for manual edits
        if (aliasesInp.value !== row.dataset.origAliases) {
            change.newAliases = aliasesInp.value;
            hasChange = true;
        }
        if (descInp.value !== row.dataset.origDesc) {
            change.newDescription = descInp.value;
            hasChange = true;
        }

        if (fixInp.value.trim() !== '') {
            change.fixInstruction = fixInp.value.trim();
            hasChange = true;
        }

        if (hasChange) {
            changes.push(change);
        }
    });

    if (changes.length === 0) {
        modal.classList.add('hidden');
        return;
    }

    godSave.textContent = "PATCHING REALITY...";
    try {
        const res = await fetch('/god_update', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({changes})
        });
        const data = await res.json();

        appendLog(data.response || "Reality patch completed.", data.state ? 'system' : 'error');
        if (data.state) updateHUD(data.state);

        godSave.textContent = "APPLY REALITY PATCH";
        modal.classList.add('hidden');
    } catch(e) {
        alert("Patch Failed.");
        godSave.textContent = "APPLY REALITY PATCH";
    }
};

if (typeof marked === 'undefined') window.marked = { parse: (t) => t };
