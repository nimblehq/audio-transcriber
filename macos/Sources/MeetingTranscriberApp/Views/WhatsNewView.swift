import SwiftUI
import MeetingTranscriberKit

/// "What's new" sheet: the changes shipped since the user last ran the app,
/// grouped by section (#155). macOS 13-compatible.
struct WhatsNewView: View {
    let entries: [ChangelogEntry]
    let onClose: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            HStack {
                Text("What's new").font(.title2.weight(.semibold))
                Spacer()
                Button("Done", action: onClose).keyboardShortcut(.defaultAction)
            }
            .padding()
            Divider()
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    ForEach(entries, id: \.version) { entry in
                        entryView(entry)
                    }
                }
                .padding()
                .frame(maxWidth: .infinity, alignment: .leading)
            }
        }
        .frame(width: 520, height: 560)
    }

    @ViewBuilder
    private func entryView(_ entry: ChangelogEntry) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(alignment: .firstTextBaseline, spacing: 8) {
                Text(entry.version).font(.headline)
                if let date = entry.date {
                    Text(date).font(.caption).foregroundStyle(.secondary)
                }
            }
            ForEach(WhatsNew.orderedSectionNames(for: entry), id: \.self) { name in
                VStack(alignment: .leading, spacing: 4) {
                    Text(name.uppercased())
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(.secondary)
                    ForEach(Array((entry.sections[name] ?? []).enumerated()), id: \.offset) { _, item in
                        HStack(alignment: .firstTextBaseline, spacing: 6) {
                            Text("•").foregroundStyle(.secondary)
                            Text(item).fixedSize(horizontal: false, vertical: true)
                        }
                    }
                }
            }
        }
    }
}

/// Sidebar bottom version label that reopens the "What's new" sheet on demand.
struct WhatsNewFooter: View {
    let version: String?
    let onTap: () -> Void

    var body: some View {
        if let version {
            Button(action: onTap) {
                Text("v\(version)")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity, alignment: .center)
            }
            .buttonStyle(.plain)
            .help("What's new")
            .padding(.vertical, 6)
        }
    }
}
