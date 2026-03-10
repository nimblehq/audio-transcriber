# Project: Meeting Transcriber

## Purpose

Internal tool for transcribing meeting recordings with speaker diarization. Built to keep all audio and transcription data local — no cloud providers involved. Privacy is the core reason this exists.

## Target Users

- **Primary:** Sales team at Nimble
- **Secondary:** Anyone at Nimble who conducts meetings (interviews, client calls)
- **Technical level:** Non-technical end users; run the app locally on their machines

## Domain

- **Meeting types:** Sales calls, client meetings, interviews
- **Languages:** English, Thai, and mixed English/Thai meetings
- **Audio sources:** Phone recordings, Plaud recording device
- **Recording length:** Typically 1–2 hours
- **Volume:** ~2–10 meetings per week

## Architecture

- **Runtime:** Fully local — runs on each user's Mac (Apple Silicon)
- **Backend:** FastAPI + WhisperX (large-v3) + PyAnnote for speaker diarization
- **Frontend:** Vanilla JS SPA, no build step
- **Storage:** File-based (JSON + audio files, no database)
- **Jobs:** In-memory dict with threading
- **Analysis:** Prompt templates that users copy-paste into an external LLM

## Constraints

- **Privacy:** No cloud deployment, no sending data to external services. All processing must remain local.
- **Hardware:** Apple Silicon Macs (MPS backend, no CUDA GPUs)
- **No auth:** Currently no authentication — acceptable because the app is local-only

## Project Stage

MVP in production use. Working but rough. Already used by the sales team day-to-day.

## Known Issues & Pain Points

- **Speaker diarization accuracy:** Wrong speaker assignments are a recurring problem
- **Transcription accuracy:** Word-level errors, especially in mixed-language (English/Thai) meetings
- **Performance:** Transcription is slow on local hardware (Apple Silicon, no discrete GPU)

## Near-term Priorities

1. Improve transcription quality (accuracy, speaker assignment, multilingual support)

## Future Considerations

- Authentication and deployment to a local/on-premise server
- Performance investigation and optimization
- Potential direct LLM integration for analysis (currently copy-paste workflow)
