import Foundation

struct SavedMessage: Codable {
    let text: String
    let isMe: Bool
    let ts: TimeInterval
}

final class ChatStore {
    static let shared = ChatStore()
    private let defaults = UserDefaults.standard

    private func key(_ convId: String) -> String { "chat.history.\(convId)" }

    func load(conversationId: String) -> [Message] {
        guard let data = defaults.data(forKey: key(conversationId)) else { return [] }
        guard let arr = try? JSONDecoder().decode([SavedMessage].self, from: data) else { return [] }
        return arr.sorted { $0.ts < $1.ts }.map { Message(text: $0.text, isMe: $0.isMe) }
    }

    func save(conversationId: String, messages: [Message]) {
        let now = Date().timeIntervalSince1970
        let arr = messages.enumerated().map { i, m in
            SavedMessage(text: m.text, isMe: m.isMe, ts: now + Double(i) / 1000.0)
        }
        if let data = try? JSONEncoder().encode(arr) {
            defaults.set(data, forKey: key(conversationId))
        }
    }
}

