import Foundation

struct ChatService {
    // Replace with your Cloud Run URL (no trailing slash)
    let baseURL = URL(string: "https://ai-kareshi-g4sue2ytha-an.a.run.app")!
    // If API_TOKEN is set on server, put same token here
    let apiToken: String? = nil // e.g. "abc"

    func send(userId: String, conversationId: String, message: String, persona: PersonaSettings? = nil) async throws -> String {
        var req = URLRequest(url: baseURL.appendingPathComponent("/api/chat"))
        req.httpMethod = "POST"
        req.addValue("application/json", forHTTPHeaderField: "Content-Type")
        if let t = apiToken { req.addValue("Bearer \(t)", forHTTPHeaderField: "Authorization") }

        var body: [String: Any] = [
            "userId": userId,
            "conversationId": conversationId,
            "message": message
        ]
        if let p = persona {
            body["persona"] = p.asDictionary()
            if let t = p.temperature { body["temperature"] = t }
        }
        req.httpBody = try JSONSerialization.data(withJSONObject: body, options: [])

        let (data, resp) = try await URLSession.shared.data(for: req)
        guard let http = resp as? HTTPURLResponse, http.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }
        let obj = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        return obj?["reply"] as? String ?? ""
    }

    // SSE streaming: calls /api/chat/stream?userId=&message=
    func stream(userId: String, conversationId: String, message: String, persona: PersonaSettings? = nil,
                onDelta: @escaping (String) -> Void,
                onDone: @escaping (String) -> Void) async throws {
        var comps = URLComponents(url: baseURL.appendingPathComponent("/api/chat/stream"), resolvingAgainstBaseURL: false)!
        var items: [URLQueryItem] = [
            .init(name: "userId", value: userId),
            .init(name: "conversationId", value: conversationId),
            .init(name: "message", value: message)
        ]
        if let p = persona {
            items.append(.init(name: "personaStyle", value: p.style.rawValue))
            items.append(.init(name: "personaFormality", value: p.formality.rawValue))
            items.append(.init(name: "personaVerbosity", value: p.verbosity.rawValue))
            items.append(.init(name: "personaEmoji", value: p.emoji ? "1" : "0"))
            if !p.instruction.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                items.append(.init(name: "personaInstruction", value: p.instruction))
            }
            if let t = p.temperature {
                items.append(.init(name: "temperature", value: String(format: "%.2f", t)))
            }
        }
        comps.queryItems = items
        guard let url = comps.url else { throw URLError(.badURL) }
        var req = URLRequest(url: url)
        req.httpMethod = "GET"
        if let t = apiToken { req.addValue("Bearer \(t)", forHTTPHeaderField: "Authorization") }
        req.addValue("text/event-stream", forHTTPHeaderField: "Accept")

        let (bytes, resp) = try await URLSession.shared.bytes(for: req)
        guard let http = resp as? HTTPURLResponse, http.statusCode == 200 else {
            throw URLError(.badServerResponse)
        }
        var buffer = ""
        var final = ""
        for try await line in bytes.lines {
            if line.isEmpty {
                // parse event block
                if buffer.contains("event: ") && buffer.contains("data: ") {
                    var ev: String = "message"
                    var dataLine: String = "{}"
                    for l in buffer.split(separator: "\n") {
                        if l.hasPrefix("event: ") { ev = String(l.dropFirst(7)).trimmingCharacters(in: .whitespaces) }
                        if l.hasPrefix("data: ") { dataLine = String(l.dropFirst(6)) }
                    }
                    if ev == "delta" {
                        if let d = try? JSONSerialization.jsonObject(with: Data(dataLine.utf8)) as? [String: Any], let delta = d["delta"] as? String {
                            final += delta
                            onDelta(delta)
                        }
                    } else if ev == "done" {
                        if let d = try? JSONSerialization.jsonObject(with: Data(dataLine.utf8)) as? [String: Any], let f = d["final"] as? String {
                            final = f
                        }
                        onDone(final)
                    }
                }
                buffer.removeAll(keepingCapacity: false)
            } else {
                buffer += line + "\n"
            }
        }
    }
}
