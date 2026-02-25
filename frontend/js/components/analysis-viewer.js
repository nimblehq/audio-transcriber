function renderAnalysisTab(container, meetingId, meetingType) {
    container.innerHTML = '<div class="loading">Loading analysis...</div>';
    loadAnalysis(container, meetingId, meetingType);
}

async function loadAnalysis(container, meetingId, meetingType) {
    try {
        const result = await API.getAnalysis(meetingId);
        if (result && result.analysis) {
            renderAnalysisContent(container, result.analysis, meetingId, meetingType);
        } else {
            renderAnalysisGenerator(container, meetingId, meetingType);
        }
    } catch {
        renderAnalysisGenerator(container, meetingId, meetingType);
    }
}

function renderAnalysisGenerator(container, meetingId, meetingType) {
    container.innerHTML = `
        <div class="analysis-generator">
            <p>Generate an AI-powered analysis of this meeting.</p>
            <div class="form-group">
                <label for="analysis-type">Meeting Type</label>
                <select id="analysis-type">
                    <option value="interview" ${meetingType === 'interview' ? 'selected' : ''}>Interview</option>
                    <option value="sales" ${meetingType === 'sales' ? 'selected' : ''}>Sales</option>
                    <option value="client" ${meetingType === 'client' ? 'selected' : ''}>Client</option>
                    <option value="other" ${meetingType === 'other' ? 'selected' : ''}>Other</option>
                </select>
            </div>
            <button class="btn btn-primary" id="generate-btn" onclick="handleGenerate('${meetingId}')">
                Generate Analysis
            </button>
        </div>
    `;
}

function renderAnalysisContent(container, markdown, meetingId, meetingType) {
    container.innerHTML = `
        <div class="analysis-content">
            <div class="analysis-actions">
                <button class="btn btn-text" onclick="handleRegenerate('${meetingId}', '${meetingType}')">Regenerate</button>
                <button class="btn btn-text" onclick="copyAnalysis()">Copy to Clipboard</button>
                <button class="btn btn-text" onclick="downloadAnalysis('${meetingId}')">Download .md</button>
            </div>
            <div class="analysis-body" id="analysis-body">${renderMarkdown(markdown)}</div>
        </div>
    `;
    container.dataset.rawMarkdown = markdown;
}

async function handleGenerate(meetingId) {
    const btn = document.getElementById('generate-btn');
    const type = document.getElementById('analysis-type').value;
    btn.disabled = true;
    btn.textContent = 'Generating...';

    try {
        const result = await API.generateAnalysis(meetingId, type);
        const container = document.getElementById('analysis-tab');
        renderAnalysisContent(container, result.analysis, meetingId, type);
        showToast('Analysis generated');
    } catch (err) {
        showToast(err.message, 'error');
        btn.disabled = false;
        btn.textContent = 'Generate Analysis';
    }
}

async function handleRegenerate(meetingId, meetingType) {
    if (!confirm('Regenerate analysis? This will replace the existing one.')) return;
    const container = document.getElementById('analysis-tab');
    container.innerHTML = '<div class="loading">Generating analysis...</div>';
    try {
        const type = meetingType || 'other';
        const result = await API.generateAnalysis(meetingId, type);
        renderAnalysisContent(container, result.analysis, meetingId, type);
        showToast('Analysis regenerated');
    } catch (err) {
        showToast(err.message, 'error');
        loadAnalysis(container, meetingId, meetingType);
    }
}

function copyAnalysis() {
    const container = document.getElementById('analysis-tab');
    const raw = container.dataset.rawMarkdown || '';
    navigator.clipboard.writeText(raw).then(() => {
        showToast('Copied to clipboard');
    }).catch(() => {
        showToast('Failed to copy', 'error');
    });
}

function downloadAnalysis(meetingId) {
    const container = document.getElementById('analysis-tab');
    const raw = container.dataset.rawMarkdown || '';
    const blob = new Blob([raw], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analysis-${meetingId}.md`;
    a.click();
    URL.revokeObjectURL(url);
}

function renderMarkdown(text) {
    // Simple markdown renderer — handles headings, bold, italic, lists, tables, blockquotes, code
    let html = escapeHtml(text);

    // Code blocks
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');

    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Headers
    html = html.replace(/^#### (.+)$/gm, '<h4>$1</h4>');
    html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');

    // Bold and italic
    html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

    // Blockquotes
    html = html.replace(/^&gt; (.+)$/gm, '<blockquote>$1</blockquote>');

    // Horizontal rules
    html = html.replace(/^---$/gm, '<hr>');

    // Tables (basic)
    html = html.replace(/^\|(.+)\|$/gm, (match, content) => {
        const cells = content.split('|').map(c => c.trim());
        if (cells.every(c => /^[-:]+$/.test(c))) return ''; // separator row
        const tag = 'td';
        return '<tr>' + cells.map(c => `<${tag}>${c}</${tag}>`).join('') + '</tr>';
    });
    html = html.replace(/(<tr>[\s\S]*?<\/tr>)/g, (match) => {
        if (!match.includes('<table>')) return '<table>' + match + '</table>';
        return match;
    });
    // Merge consecutive tables
    html = html.replace(/<\/table>\s*<table>/g, '');

    // Unordered lists
    html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>[\s\S]*?<\/li>)/g, (match) => '<ul>' + match + '</ul>');
    html = html.replace(/<\/ul>\s*<ul>/g, '');

    // Checkboxes
    html = html.replace(/\[ \]/g, '☐');
    html = html.replace(/\[x\]/gi, '☑');

    // Paragraphs
    html = html.replace(/\n\n/g, '</p><p>');
    html = '<p>' + html + '</p>';
    html = html.replace(/<p>\s*<(h[1-4]|ul|ol|table|blockquote|pre|hr)/g, '<$1');
    html = html.replace(/<\/(h[1-4]|ul|ol|table|blockquote|pre|hr)>\s*<\/p>/g, '</$1>');
    html = html.replace(/<p>\s*<\/p>/g, '');

    return html;
}
