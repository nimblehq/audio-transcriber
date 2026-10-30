import Foundation
import MeetingTranscriberKit

private let whatsNewDecoder = JSONCoding.makeDecoder()

private func decodeChangelog(_ json: String) -> ChangelogResponse? {
    try? whatsNewDecoder.decode(ChangelogResponse.self, from: Data(json.utf8))
}

func runWhatsNewTests() {
    suite("ChangelogResponse decoding") {
        let json = """
        {"current_version":"1.2.0","entries":[
          {"version":"1.2.0","date":"2026-05-08","sections":{"Added":["A feature."],"Fixed":["A fix."]}},
          {"version":"1.1.0","date":"2026-02-26","sections":{"Changed":["A change."]}}]}
        """
        let response = decodeChangelog(json)
        expectEqual(response?.currentVersion, "1.2.0", "current_version maps via snake_case")
        expectEqual(response?.entries.count, 2, "two entries")
        expectEqual(response?.entries[0].sections["Added"] ?? [], ["A feature."], "section bullets")
        expectEqual(response?.entries[0].date, "2026-05-08", "date parsed")
    }

    suite("ChangelogResponse decoding — empty/degraded") {
        let response = decodeChangelog(#"{"current_version":null,"entries":[]}"#)
        expectNil(response?.currentVersion, "null current_version → nil")
        expectEqual(response?.entries.count, 0, "no entries")
    }

    suite("compareVersions") {
        expect(WhatsNew.compareVersions("1.2.0", "1.1.0") > 0, "1.2.0 > 1.1.0")
        expect(WhatsNew.compareVersions("1.1.0", "1.2.0") < 0, "1.1.0 < 1.2.0")
        expectEqual(WhatsNew.compareVersions("1.2.0", "1.2.0"), 0, "equal")
        expect(WhatsNew.compareVersions("1.10.0", "1.9.0") > 0, "numeric, not lexical: 1.10 > 1.9")
        expect(WhatsNew.compareVersions("2.0", "1.9.9") > 0, "shorter major wins")
        expectEqual(WhatsNew.compareVersions("1.0", "1.0.0"), 0, "missing component counts as 0")
    }

    suite("entriesSince — forward range only") {
        let response = ChangelogResponse(currentVersion: "1.2.0", entries: [
            ChangelogEntry(version: "1.2.0", date: nil, sections: [:]),
            ChangelogEntry(version: "1.1.0", date: nil, sections: [:]),
            ChangelogEntry(version: "1.0.0", date: nil, sections: [:]),
        ])
        let since = WhatsNew.entriesSince(lastSeen: "1.0.0", in: response)
        expectEqual(since.map { $0.version }, ["1.2.0", "1.1.0"], "only versions newer than last-seen")
    }

    suite("entriesSince — first run is silent") {
        let response = ChangelogResponse(currentVersion: "1.2.0", entries: [
            ChangelogEntry(version: "1.2.0", date: nil, sections: [:]),
        ])
        expectEqual(WhatsNew.entriesSince(lastSeen: nil, in: response).count, 0, "nil last-seen → nothing")
    }

    suite("entriesSince — downgrade / caught up shows nothing") {
        let response = ChangelogResponse(currentVersion: "1.2.0", entries: [
            ChangelogEntry(version: "1.2.0", date: nil, sections: [:]),
        ])
        expectEqual(WhatsNew.entriesSince(lastSeen: "1.2.0", in: response).count, 0, "equal → nothing")
        expectEqual(WhatsNew.entriesSince(lastSeen: "1.3.0", in: response).count, 0, "newer last-seen → nothing")
    }

    suite("entriesSince — nil current version shows nothing") {
        let response = ChangelogResponse(currentVersion: nil, entries: [])
        expectEqual(WhatsNew.entriesSince(lastSeen: "1.0.0", in: response).count, 0, "no current version → nothing")
    }

    suite("orderedSectionNames — Keep a Changelog order") {
        let entry = ChangelogEntry(version: "1.0.0", date: nil, sections: [
            "Fixed": ["f"], "Added": ["a"], "Security": ["s"], "Custom": ["c"],
        ])
        expectEqual(WhatsNew.orderedSectionNames(for: entry), ["Added", "Fixed", "Security", "Custom"],
                    "known sections in canonical order, unknown last")
    }
}
