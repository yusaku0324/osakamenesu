import Foundation

struct Conversation: Identifiable, Codable, Equatable {
    let id: String
    var title: String
    var updatedAt: TimeInterval
}

final class ConversationsStore: ObservableObject {
    static let shared = ConversationsStore()
    @Published private(set) var items: [Conversation] = []

    private let defaults = UserDefaults.standard
    private let key = "chat.conversations"

    init() {
        load()
        if items.isEmpty {
            // Ensure at least one conversation exists
            let first = Conversation(id: "default", title: "会話 1", updatedAt: Date().timeIntervalSince1970)
            items = [first]
            persist()
        }
    }

    func load() {
        if let data = defaults.data(forKey: key),
           let arr = try? JSONDecoder().decode([Conversation].self, from: data) {
            items = arr.sorted { $0.updatedAt > $1.updatedAt }
        }
    }

    func persist() {
        if let data = try? JSONEncoder().encode(items) {
            defaults.set(data, forKey: key)
        }
    }

    func add(title: String? = nil) -> Conversation {
        let id = UUID().uuidString
        let num = items.count + 1
        let t = title ?? "会話 \(num)"
        let c = Conversation(id: id, title: t, updatedAt: Date().timeIntervalSince1970)
        items.insert(c, at: 0)
        persist()
        return c
    }

    func remove(id: String) {
        items.removeAll { $0.id == id }
        persist()
    }

    func rename(id: String, title: String) {
        guard let idx = items.firstIndex(where: { $0.id == id }) else { return }
        items[idx].title = title
        persist()
    }

    func touch(id: String) {
        guard let idx = items.firstIndex(where: { $0.id == id }) else { return }
        items[idx].updatedAt = Date().timeIntervalSince1970
        items.sort { $0.updatedAt > $1.updatedAt }
        persist()
    }
}

