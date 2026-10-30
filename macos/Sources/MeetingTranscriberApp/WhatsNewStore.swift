import Foundation
import MeetingTranscriberKit

/// Drives the "What's new" sheet (#155). On launch it shows the changes between
/// the user's last-seen version and the current one; the first-ever launch stores
/// a silent baseline so existing users aren't shown the whole history. The footer
/// version label reopens the full history on demand.
@MainActor
final class WhatsNewStore: ObservableObject {
    @Published var isPresented = false
    @Published private(set) var entries: [ChangelogEntry] = []
    @Published private(set) var currentVersion: String?

    private let client: APIClient
    private let preferences: Preferences

    init(client: APIClient, preferences: Preferences = Preferences()) {
        self.client = client
        self.preferences = preferences
    }

    /// Launch check. Swallows any fetch error so startup is never blocked. The
    /// baseline is written only after a successful fetch with a real current
    /// version, so a failed/empty response never silently suppresses the panel.
    func checkOnLaunch() async {
        guard let response = try? await client.changelog(),
              let current = response.currentVersion else { return }

        currentVersion = current
        let lastSeen = preferences.lastSeenChangelogVersion
        preferences.lastSeenChangelogVersion = current

        let toShow = WhatsNew.entriesSince(lastSeen: lastSeen, in: response)
        guard !toShow.isEmpty else { return }
        entries = toShow
        isPresented = true
    }

    /// Manual reopen from the footer version label: show the full history.
    func showManually() async {
        guard let response = try? await client.changelog() else { return }
        currentVersion = response.currentVersion
        if let current = response.currentVersion {
            preferences.lastSeenChangelogVersion = current
        }
        entries = response.entries
        isPresented = true
    }
}
