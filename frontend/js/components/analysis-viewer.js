function renderAnalysisTab(container, meetingId, meetingType) {
    if (meetingId) container.dataset.meetingId = meetingId;
    container.innerHTML = `
        ${renderUnnamedSpeakersWarning()}
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
    const tabContainer = document.getElementById('analysis-tab');
    const meetingId = tabContainer ? tabContainer.dataset.meetingId : '';
    btn.disabled = true;
    btn.textContent = 'Generating...';

    try {
        const [templateResult, audioContextResult] = await Promise.all([
            API.getTemplate(type),
            meetingId ? API.getAnalysisContext(meetingId) : Promise.resolve({ context: '' }),
        ]);
        const transcript = buildPlainTextTranscript();
        const context = getMeetingContext();
        const audioContext = audioContextResult.context || '';
        let prompt = templateResult.template;
        if (audioContext) {
            prompt = prompt.replace('[AUDIO ANALYSIS CONTEXT]', audioContext);
        } else {
            // Strip the placeholder line entirely so the prompt remains
            // byte-identical to the pre-feature output (BR-4.4).
            prompt = prompt.replace('[AUDIO ANALYSIS CONTEXT]\n', '');
        }
        if (context) {
            prompt = prompt.replace('[MEETING CONTEXT]', '## Meeting Context\n\n' + context);
        } else {
            prompt = prompt.replace('[MEETING CONTEXT]\n\n', '');
        }
        prompt = prompt.replace('[PASTE TRANSCRIPT HERE]', transcript);

        renderPromptContent(tabContainer, prompt);
    } catch (err) {
        showToast(err.message, 'error');
        btn.disabled = false;
        btn.textContent = 'Generate Prompt';
    }
}

function getMeetingContext() {
    const textarea = document.getElementById('meeting-context');
    return textarea ? textarea.value.trim() : '';
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
        ${renderUnnamedSpeakersWarning()}
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

// Reads `window._speakerEditorState`, which is populated by
// `renderSegments()` in transcript-viewer.js when the meeting loads.
// If transcript-viewer.js changes that contract, update this read site.
function getUnnamedSpeakersInfo() {
    const state = window._speakerEditorState;
    if (!state || !state.speakerIds || !state.speakers) return null;
    const total = state.speakerIds.length;
    const unnamed = state.speakerIds.filter(id =>
        isUnidentifiedSpeaker(state.speakers[id] || id)
    ).length;
    return { unnamed, total };
}

function renderUnnamedSpeakersWarning() {
    const info = getUnnamedSpeakersInfo();
    if (!info || info.unnamed === 0) return '';
    const { unnamed, total } = info;
    const verb = unnamed === 1 ? 'is' : 'are';
    const noun = unnamed === 1 ? 'speaker' : 'speakers';
    return `
        <div class="overview-notice analysis-warning" role="status">
            ${unnamed} of ${total} ${noun} ${verb} still unnamed. Rename them on the Transcript tab — the generated prompt will use raw labels like <code>SPEAKER_00</code> until you do.
        </div>
    `;
}

function copyPrompt() {
    const container = document.getElementById('analysis-tab');
    const raw = container.dataset.rawPrompt || '';
    copyToClipboard(raw);
}
