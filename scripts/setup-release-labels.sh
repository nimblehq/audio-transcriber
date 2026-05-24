#!/usr/bin/env bash
# Idempotent setup script for release-triggering labels.
#
# Run once per repo (or after deleting a label by accident). Safe to re-run
# — `gh label create … || true` swallows the "already exists" error.
#
# Canonical place to add future release-trigger labels. If you extend the
# label map in .releaserc.js, also add the new label here.

set -euo pipefail

# breaking → major version bump (manually applied; not emitted by the
# auto-labeler). Color #B60205 is a darker red than `bug`'s #D73A4A so the
# two are visually distinguishable in the PR list.
gh label create breaking \
  --color B60205 \
  --description "Breaking change — bumps major version on next release" \
  || true

# Defensive re-creation of the labels the release workflow and auto-labeler
# rely on. These already exist on nimblehq/audio-transcriber, so `gh label
# create` will no-op via `|| true`. Listed here so a future clone, fork, or
# accidental deletion can be recovered by re-running this script.
gh label create feature \
  --color 0E8A16 \
  --description "New feature or enhancement" \
  || true
gh label create bug \
  --color D73A4A \
  --description "Something isn't working" \
  || true
gh label create chore \
  --color EDEDED \
  --description "Maintenance or housekeeping task" \
  || true
gh label create documentation \
  --color 0075CA \
  --description "Improvements or additions to documentation" \
  || true

echo "Release labels are set up."
