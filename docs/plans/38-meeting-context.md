# Plan: Provide context with each meeting

**Story**: #38
**Spec**: `docs/specs/meeting-context.md`
**Branch**: `feature/38-meeting-context`
**Date**: 2026-04-08
**Mode**: Standard — straightforward CRUD addition, no complex logic needing TDD

## Technical Decisions

### TD-1: Context stored as plain string in metadata.json
- **Context**: Need to persist free-text context per meeting
- **Decision**: Add `context: str = ""` to MeetingMetadata Pydantic model
- **Alternatives considered**: Separate context file per meeting — unnecessary complexity for a single string field

### TD-2: Template placeholder approach for prompt injection
- **Context**: Need to inject context into analysis prompts
- **Decision**: Add `[MEETING CONTEXT]` placeholder in all templates, replace in frontend JS
- **Alternatives considered**: Backend-side injection — would require API changes to pass context to template endpoint; frontend replacement is simpler and consistent with existing `[PASTE TRANSCRIPT HERE]` pattern

## Files to Create or Modify

- `backend/schemas.py` — Add `context` field to MeetingMetadata and MeetingUpdate
- `backend/routers/meetings.py` — Accept `context` Form field in create_meeting, handle in update_meeting
- `frontend/js/api.js` — Pass `context` param in createMeeting
- `frontend/js/components/upload.js` — Add context textarea to upload form
- `frontend/js/components/transcript-viewer.js` — Display editable context in meeting detail
- `frontend/js/components/analysis-viewer.js` — Inject context into generated prompts
- `templates/*.md` (all 5) — Add `[MEETING CONTEXT]` placeholder

## Approach per AC

### AC 1: Upload form has an optional "Context" textarea
Add textarea after meeting type, before preprocessing checkbox. Send value in FormData.

### AC 2: Context is saved in meeting metadata and returned by GET /api/meetings/{id}
Add `context: str = ""` to MeetingMetadata. Accept `context` Form field in POST. GET already returns full metadata.

### AC 3: Context is editable from the meeting detail view via PATCH
Add `context: str | None = None` to MeetingUpdate. Render editable textarea in transcript-viewer with save-on-blur.

### AC 4: Generated analysis prompts include a `## Meeting Context` section when context is non-empty
Add `[MEETING CONTEXT]` placeholder in templates. In analysis-viewer.js, replace with context section or remove line.

### AC 5: Existing meetings without context continue to work (empty default)
Pydantic default `""` handles missing field in old metadata.json files.

## Commit Sequence

1. Add `context` field to backend schemas and API endpoint
2. Add context textarea to upload form and API client
3. Add context display/edit in meeting detail view
4. Add `[MEETING CONTEXT]` placeholder to templates and inject context in analysis prompt generation

## Risks and Trade-offs

- No character limit on context field (per spec: user responsibility)
- All templates must include the placeholder; new templates added later must follow suit

## Deviations from Spec

- None planned

## Deviations from Plan

_Populated after implementation._
