/* Shared helpers for rendering audio analysis insights.
 * Mirrors a subset of backend/services/analysis_context.py — keep the
 * agreement phrases and mismatch emotions in sync with the Python file.
 */

const AudioInsights = (() => {
    const AGREEMENT_PHRASES = [
        'works for me', 'sounds good', "that's fine", 'thats fine',
        'no concerns', 'no issues', 'no problem', 'i agree', 'agreed',
        'sure thing', 'fine by me', 'looks good', 'all good',
        'happy with that', "i'm good", 'im good', 'makes sense',
        "i'm okay with", 'im okay with', "i'm fine with", 'im fine with',
    ];

    const MISMATCH_EMOTIONS = new Set(['frustrated', 'uncertain']);
    const ENERGY_POSITIVE = new Set(['engaged', 'confident']);
    const ENERGY_NEGATIVE = new Set(['disengaged', 'frustrated']);
    const ENERGY_WINDOW_SECONDS = 300;

    const EMOTION_LABELS = {
        neutral: 'Neutral',
        confident: 'Confident',
        frustrated: 'Frustrated',
        uncertain: 'Uncertain',
        engaged: 'Engaged',
        disengaged: 'Disengaged',
    };

    function hasCompletedAnalysis(meta, audioAnalysis) {
        return Boolean(meta && meta.audio_analysis_enabled && audioAnalysis && audioAnalysis.status === 'completed');
    }

    function indexBySegment(audioAnalysis) {
        const map = {};
        if (!audioAnalysis) return map;
        const ensure = (id) => (map[id] = map[id] || { emotion: null, prosody: null, interaction: null });
        (audioAnalysis.emotions || []).forEach(e => { ensure(e.segment_id).emotion = e; });
        (audioAnalysis.prosody || []).forEach(p => { ensure(p.segment_id).prosody = p; });
        (audioAnalysis.segment_interactions || []).forEach(s => { ensure(s.segment_id).interaction = s; });
        return map;
    }

    function isWordToneMismatch(emotion, segmentText) {
        if (!emotion || !MISMATCH_EMOTIONS.has(emotion.primary_emotion)) return false;
        const lower = (segmentText || '').toLowerCase();
        return AGREEMENT_PHRASES.some(p => lower.includes(p));
    }

    function formatProsodyTooltip(prosody) {
        if (!prosody) return '';
        const fmt = (n, d = 2) => (Number.isFinite(n) ? n.toFixed(d) : '–');
        return [
            `Volume: ${fmt(prosody.volume_mean)} (var ${fmt(prosody.volume_variance)})`,
            `Pitch: ${fmt(prosody.pitch_mean, 0)} Hz (var ${fmt(prosody.pitch_variance, 0)})`,
            `Speaking rate: ${fmt(prosody.speaking_rate, 0)} wpm`,
            `Pause ratio: ${fmt(prosody.pause_ratio)}`,
        ].join('\n');
    }

    function hasInteractionMarker(interaction) {
        if (!interaction) return false;
        return Boolean(interaction.preceded_by_interruption) || (interaction.hesitation_before || 0) > 0;
    }

    function interactionTooltip(interaction) {
        const parts = [];
        if (interaction.preceded_by_interruption) parts.push('Preceded by an interruption');
        if (interaction.followed_by_interruption) parts.push('Followed by an interruption');
        if ((interaction.hesitation_before || 0) > 0) {
            parts.push(`Hesitated ${interaction.hesitation_before.toFixed(1)}s before speaking`);
        }
        return parts.join('\n');
    }

    function energyScore(emotion) {
        if (!emotion) return 0;
        if (ENERGY_POSITIVE.has(emotion.primary_emotion)) return emotion.confidence;
        if (ENERGY_NEGATIVE.has(emotion.primary_emotion)) return -emotion.confidence;
        return 0;
    }

    function buildEnergyTrajectory(emotions) {
        if (!emotions || emotions.length === 0) return [];
        const end = Math.max(...emotions.map(e => e.end));
        if (end <= 0) return [];
        const nWindows = Math.max(1, Math.floor(end / ENERGY_WINDOW_SECONDS) + 1);
        const buckets = Array.from({ length: nWindows }, () => []);
        emotions.forEach(e => {
            const idx = Math.min(Math.floor(e.start / ENERGY_WINDOW_SECONDS), nWindows - 1);
            buckets[idx].push(energyScore(e));
        });
        return buckets.map((scores, i) => ({
            index: i,
            start: i * ENERGY_WINDOW_SECONDS,
            end: (i + 1) * ENERGY_WINDOW_SECONDS,
            score: scores.length ? scores.reduce((a, b) => a + b, 0) / scores.length : null,
            count: scores.length,
        }));
    }

    return {
        AGREEMENT_PHRASES,
        MISMATCH_EMOTIONS,
        EMOTION_LABELS,
        ENERGY_WINDOW_SECONDS,
        hasCompletedAnalysis,
        indexBySegment,
        isWordToneMismatch,
        formatProsodyTooltip,
        hasInteractionMarker,
        interactionTooltip,
        energyScore,
        buildEnergyTrajectory,
    };
})();
