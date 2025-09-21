import Foundation

struct Message: Identifiable, Equatable {
    let id = UUID()
    var text: String
    let isMe: Bool
    var read: Bool = false // for "既読"表示（送信者のメッセージにのみ使用）
}

// ペルソナ切替用の定義
enum PersonaStyle: String, CaseIterable, Codable {
    case business    // 業務的/簡潔
    case casual      // カジュアル/親しみ
    case teacher     // 教師的/丁寧
    case brainstorm  // ブレスト/発散

    var label: String {
        switch self {
        case .business: return "業務的"
        case .casual: return "カジュアル"
        case .teacher: return "教師的"
        case .brainstorm: return "ブレスト"
        }
    }
}

enum Formality: String, CaseIterable, Codable {
    case polite   // 敬語
    case casual   // タメ口

    var label: String { self == .polite ? "敬語" : "カジュアル" }
}

enum Verbosity: String, CaseIterable, Codable {
    case concise  // 簡潔
    case detailed // 詳しい

    var label: String { self == .concise ? "簡潔" : "詳しい" }
}

struct PersonaSettings: Codable, Equatable {
    var style: PersonaStyle = .casual
    var formality: Formality = .polite
    var verbosity: Verbosity = .concise
    var emoji: Bool = false
    var instruction: String = "" // 自由入力の追加指示
    var temperature: Double? = nil // 0.0 - 1.0

    func asDictionary() -> [String: Any] {
        var dict: [String: Any] = [
            "style": style.rawValue,
            "formality": formality.rawValue,
            "verbosity": verbosity.rawValue,
            "emoji": emoji
        ]
        if !instruction.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            dict["instruction"] = instruction
        }
        return dict
    }
}
