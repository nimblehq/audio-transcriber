function formatDuration(seconds) {
    if (!seconds) return '--:--';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
    return `${m}:${String(s).padStart(2, '0')}`;
}

function formatTimestamp(seconds) {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

function formatDate(dateStr) {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.classList.add('toast-visible'), 10);
    setTimeout(() => {
        toast.classList.remove('toast-visible');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

const SPEAKER_COLORS = [
    '#4A90D9', '#D94A4A', '#4AD97A', '#D9A84A',
    '#9B4AD9', '#4AD9D9', '#D94A9B', '#7AD94A',
];

function getSpeakerColor(index) {
    return SPEAKER_COLORS[index % SPEAKER_COLORS.length];
}

function getRecentSpeakerNames() {
    try {
        return JSON.parse(localStorage.getItem('recentSpeakerNames') || '[]');
    } catch {
        return [];
    }
}

function addRecentSpeakerName(name) {
    if (!name.trim()) return;
    let names = getRecentSpeakerNames();
    names = names.filter(n => n !== name);
    names.unshift(name);
    names = names.slice(0, 10);
    localStorage.setItem('recentSpeakerNames', JSON.stringify(names));
}

function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(() => {
            showToast('Copied to clipboard');
        }).catch(() => {
            fallbackCopy(text);
        });
    } else {
        fallbackCopy(text);
    }
}

function fallbackCopy(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    try {
        document.execCommand('copy');
        showToast('Copied to clipboard');
    } catch {
        showToast('Failed to copy', 'error');
    }
    document.body.removeChild(textarea);
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
