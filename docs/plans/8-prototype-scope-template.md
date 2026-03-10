# Plan: Prototype Scope Template

**Story**: GitHub Issue #8
**Spec**: docs/specs/prototype-scope-template.md
**Branch**: feature/prototype-scope-template
**Date**: 2026-03-10
**Mode**: Standard — no test infrastructure exists; change is 3 files with minimal logic

## Technical Decisions

### TD-1: Template available for all meeting types without auto-select
- **Context**: The template must appear for all meeting types (BR-1)
- **Decision**: Add it as a regular dropdown option without any `selected` logic tied to meeting type
- **Alternatives considered**: Auto-selecting based on meeting type — unnecessary since this is a cross-cutting template

## Files to Create or Modify

- `templates/prototype_scope.md` — New LLM prompt template with all 8 required sections
- `backend/routers/analysis.py` — Add `"prototype": "prototype_scope.md"` to TEMPLATE_FILES dict
- `frontend/js/components/analysis-viewer.js` — Add Prototype Scope option to dropdown

## Approach per AC

### AC 1: Dropdown option appears for all meeting types
Add `<option value="prototype">Prototype Scope</option>` to the select element (not conditioned on meetingType).

### AC 2: Structured output with required sections
Template prompt instructs LLM to produce: Project Overview, Brand & Visual Direction, Pages & Navigation, Core Features (5-7), Sample Data & Content, User Flows, Non-Goals, Build Phases.

### AC 3-4: Real content extraction and priority-based features
Template prompt contains explicit instructions to extract real content and prioritize by client emphasis.

### AC 5: Insufficient detail handling
Template prompt includes fallback instruction for when transcript lacks product/feature discussion.

### AC 6: Thai/mixed language → English
Template prompt includes language instruction.

### AC 7: Copy-paste ready for AI coding tools
Output format designed as structured markdown ready for Replit Agent / similar tools.

## Commit Sequence

1. Add prototype scope template file
2. Wire template in backend and frontend

## Risks and Trade-offs

- None — follows the exact pattern of 4 existing templates

## Deviations from Spec

- None anticipated

## Deviations from Plan

_Populated after implementation._
