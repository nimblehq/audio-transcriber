// semantic-release configuration.
//
// Triggered by .github/workflows/release.yml on push to main.
// Reads merged-PR labels to compute the next version bump, then creates a
// bare-semver GitHub Release with auto-generated notes from PR titles.
//
// Label map (only labels listed here trigger a release):
//   - breaking → major
//   - feature  → minor
//   - bug      → patch
// Any other label (chore, documentation, etc.) is ignored. A PR with no
// release-triggering label contributes no version bump. If a release window
// contains only non-mapped labels, semantic-release exits with
// "no release published" — this is expected, not an error.
//
// When a PR carries multiple release-triggering labels (e.g., breaking +
// feature), the highest bump wins: major > minor > patch.

module.exports = {
  branches: ['main'],
  tagFormat: '${version}',
  plugins: [
    [
      '@bobvanderlinden/semantic-release-pull-request-analyzer',
      {
        labels: {
          breaking: 'major',
          feature: 'minor',
          bug: 'patch',
        },
      },
    ],
    [
      '@semantic-release/github',
      {
        successComment: false,
        releasedLabels: false,
      },
    ],
  ],
};
