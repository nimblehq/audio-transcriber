function renderAnalysisTab(container, meetingId, meetingType) {
    container.innerHTML = `
        <div class="analysis-generator">
            <p>Select a template to generate a prompt you can paste into any LLM for analysis.</p>
            <div class="form-group">
                <label for="analysis-type">Template</label>
                <select id="analysis-type">
                    <option value="interview" ${meetingType === 'interview' ? 'selected' : ''}>Interview</option>
                    <option value="sales" ${meetingType === 'sales' ? 'selected' : ''}>Sales</option>
                    <option value="client" ${meetingType === 'client' ? 'selected' : ''}>Client</option>
                    <option value="other" ${meetingType === 'other' ? 'selected' : ''}>Other</option>
                    <option value="prototype">Prototype Scope</option>
                </select>
            </div>
            <button class="btn btn-primary" id="generate-prompt-btn" onclick="handleGeneratePrompt()">
                Generate Prompt
            </button>
        </div>
    `;
}

async function handleGeneratePrompt() {
    const btn = document.getElementById('generate-prompt-btn');
    const type = document.getElementById('analysis-type').value;
    btn.disabled = true;
    btn.textContent = 'Generating...';

    try {
        const result = await API.getTemplate(type);
        const transcript = buildPlainTextTranscript();
        const prompt = result.template.replace('[PASTE TRANSCRIPT HERE]', transcript);

        const container = document.getElementById('analysis-tab');
        renderPromptContent(container, prompt);
    } catch (err) {
        showToast(err.message, 'error');
        btn.disabled = false;
        btn.textContent = 'Generate Prompt';
    }
}

function buildPlainTextTranscript() {
    const state = window._speakerEditorState;
    if (!state) return '';

    const segments = document.querySelectorAll('#segments-container .segment');
    const lines = [];

    segments.forEach(seg => {
        const speakerId = seg.querySelector('.speaker-label').dataset.speaker;
        const speakerName = state.speakers[speakerId] || speakerId;
        const time = seg.querySelector('.segment-time').textContent;
        const text = seg.querySelector('.segment-text').textContent;
        lines.push(`[${time}] ${speakerName}: ${text}`);
    });

    return lines.join('\n');
}

function renderPromptContent(container, prompt) {
    container.innerHTML = `
        <div class="analysis-content">
            <div class="analysis-actions">
                <button class="btn btn-primary" onclick="copyPrompt()">Copy to clipboard</button>
                <button class="btn btn-text" onclick="renderAnalysisTab(this.closest('.tab-content'), '', document.getElementById('analysis-type')?.value || 'other')">Back</button>
            </div>
            <pre class="plaintext-content">${escapeHtml(prompt)}</pre>
        </div>
    `;
    container.dataset.rawPrompt = prompt;
}

function copyPrompt() {
    const container = document.getElementById('analysis-tab');
    const raw = container.dataset.rawPrompt || '';
    copyToClipboard(raw);
}
