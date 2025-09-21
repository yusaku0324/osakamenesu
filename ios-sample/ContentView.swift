import SwiftUI

struct ContentView: View {
    @StateObject var convs = ConversationsStore.shared
    @State private var editTitle: String = ""
    @State private var renamingId: String? = nil

    var body: some View {
        NavigationView {
            List {
                ForEach(convs.items) { c in
                    NavigationLink(destination: ChatView(conversationId: c.id)) {
                        VStack(alignment: .leading, spacing: 4) {
                            HStack {
                                Text(c.title).font(.headline)
                                Spacer()
                                Text(Date(timeIntervalSince1970: c.updatedAt), style: .time)
                                    .font(.caption).foregroundColor(.secondary)
                            }
                            Text(c.id).font(.caption2).foregroundColor(.secondary)
                        }
                    }
                    .swipeActions {
                        Button(role: .destructive) { convs.remove(id: c.id) } label: { Label("削除", systemImage: "trash") }
                        Button { renamingId = c.id; editTitle = c.title } label: { Label("名称変更", systemImage: "pencil") }
                    }
                }
            }
            .navigationTitle("会話一覧")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { _ = convs.add() }) { Image(systemName: "plus") }
                }
            }
            .sheet(item: $renamingId) { id in
                RenameView(title: $editTitle, onSave: {
                    convs.rename(id: id, title: editTitle)
                    renamingId = nil
                }, onCancel: { renamingId = nil })
            }
        }
    }
}

private struct RenameView: View {
    @Binding var title: String
    let onSave: () -> Void
    let onCancel: () -> Void
    var body: some View {
        NavigationView {
            Form {
                TextField("タイトル", text: $title)
            }
            .navigationTitle("名称変更")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("キャンセル", action: onCancel) }
                ToolbarItem(placement: .confirmationAction) { Button("保存", action: onSave).disabled(title.trimmingCharacters(in: .whitespaces).isEmpty) }
            }
        }
    }
}

