import Foundation

/// Pure decision logic for the "What's new" sheet — the Swift analogue of the
/// web client's `whats-new.js`. Kept byte-for-byte consistent with it so the two
/// front ends never diverge: numeric dotted version compare, a strictly-newer
/// filter, and the Keep a Changelog section order.
public enum WhatsNew {
    /// Keep a Changelog section order; unknown sections sort after, alphabetically.
    static let sectionOrder = ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"]

    /// Numeric dotted compare. Returns >0 if a>b, <0 if a<b, 0 if equal.
    /// Non-numeric or missing components count as 0, so odd values never crash.
    public static func compareVersions(_ a: String, _ b: String) -> Int {
        let pa = a.split(separator: ".", omittingEmptySubsequences: false).map { Int($0) ?? 0 }
        let pb = b.split(separator: ".", omittingEmptySubsequences: false).map { Int($0) ?? 0 }
        for i in 0..<max(pa.count, pb.count) {
            let diff = (i < pa.count ? pa[i] : 0) - (i < pb.count ? pb[i] : 0)
            if diff != 0 { return diff }
        }
        return 0
    }

    /// Entries strictly newer than `lastSeen`, up to the current version. Empty
    /// when the response has no current version, or `lastSeen` is nil (first run)
    /// or not older than current (downgrade / already caught up).
    public static func entriesSince(lastSeen: String?, in response: ChangelogResponse) -> [ChangelogEntry] {
        guard let current = response.currentVersion else { return [] }
        guard let lastSeen, compareVersions(lastSeen, current) < 0 else { return [] }
        return response.entries.filter { compareVersions($0.version, lastSeen) > 0 }
    }

    /// Section names of an entry in stable display order.
    public static func orderedSectionNames(for entry: ChangelogEntry) -> [String] {
        entry.sections.keys.sorted { lhs, rhs in
            let li = sectionOrder.firstIndex(of: lhs)
            let ri = sectionOrder.firstIndex(of: rhs)
            switch (li, ri) {
            case let (l?, r?): return l < r
            case (_?, nil): return true
            case (nil, _?): return false
            default: return lhs < rhs
            }
        }
    }
}
