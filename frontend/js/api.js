const API = {
    async listMeetings() {
        const res = await fetch('/api/meetings');
        if (!res.ok) throw new Error('Failed to fetch meetings');
        return res.json();
    },

    async getMeeting(id) {
        const res = await fetch(`/api/meetings/${id}`);
        if (!res.ok) throw new Error('Failed to fetch meeting');
        return res.json();
    },

    async createMeeting(file, title, meetingType, language, numSpeakers) {
        const form = new FormData();
        form.append('file', file);
        form.append('title', title || '');
        form.append('meeting_type', meetingType || 'other');
        form.append('language', language || 'auto');
        form.append('num_speakers', numSpeakers || 'auto');
        const res = await fetch('/api/meetings', { method: 'POST', body: form });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Upload failed');
        }
        return res.json();
    },

    async updateMeeting(id, data) {
        const res = await fetch(`/api/meetings/${id}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error('Failed to update meeting');
        return res.json();
    },

    async retryTranscription(id) {
        const res = await fetch(`/api/meetings/${id}/retry`, { method: 'POST' });
        if (!res.ok) throw new Error('Failed to retry transcription');
        return res.json();
    },

    async deleteMeeting(id) {
        const res = await fetch(`/api/meetings/${id}`, { method: 'DELETE' });
        if (!res.ok) throw new Error('Failed to delete meeting');
        return res.json();
    },

    async getJob(jobId) {
        const res = await fetch(`/api/jobs/${jobId}`);
        if (!res.ok) throw new Error('Failed to fetch job status');
        return res.json();
    },

    async getAnalysis(meetingId) {
        const res = await fetch(`/api/meetings/${meetingId}/analysis`);
        if (res.status === 404) return null;
        if (!res.ok) throw new Error('Failed to fetch analysis');
        return res.json();
    },

    async generateAnalysis(meetingId, meetingType) {
        const res = await fetch(`/api/meetings/${meetingId}/analysis`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ meeting_type: meetingType || null }),
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Analysis generation failed');
        }
        return res.json();
    },

    async updateSegmentSpeaker(meetingId, segmentId, speakerName) {
        const res = await fetch(`/api/meetings/${meetingId}/segments/speaker`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ segment_id: segmentId, speaker_name: speakerName }),
        });
        if (!res.ok) throw new Error('Failed to update segment speaker');
        return res.json();
    },

    audioUrl(meetingId) {
        return `/api/meetings/${meetingId}/audio`;
    },
};
