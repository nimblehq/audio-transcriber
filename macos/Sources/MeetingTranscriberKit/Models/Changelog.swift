import Foundation

/// Released changelog entries served by `GET /api/changelog`, parsed from the
/// hand-maintained CHANGELOG.md. Powers the native "What's new" sheet (#155).
/// Entries are newest-first and exclude the `[Unreleased]` section. A missing
/// changelog yields `currentVersion == nil` and `entries == []` (HTTP 200).
public struct ChangelogResponse: Codable, Equatable {
    /// Latest released version, or nil when the changelog is absent/empty.
    public let currentVersion: String?
    public let entries: [ChangelogEntry]

    public init(currentVersion: String?, entries: [ChangelogEntry]) {
        self.currentVersion = currentVersion
        self.entries = entries
    }
}

/// One released version with its change bullets grouped by section name
/// (Added / Changed / Fixed / ...). `sections` is an unordered map on the wire;
/// use `WhatsNew.orderedSectionNames(for:)` for a stable display order.
public struct ChangelogEntry: Codable, Equatable {
    public let version: String
    public let date: String?
    public let sections: [String: [String]]

    public init(version: String, date: String?, sections: [String: [String]]) {
        self.version = version
        self.date = date
        self.sections = sections
    }
}
