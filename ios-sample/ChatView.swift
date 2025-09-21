import SwiftUI

struct ChatView: View {
    @State private var userId = UUID().uuidString
    @State private var input = ""
    @State private var items: [Message] = []
    let service = ChatService()
    let conversationId: String
    @State private var isTyping: Bool = false
    @State private var lastUserIndex: Int? = nil
    @State private var showPersonaSheet: Bool = false

    // Persist persona selection
    @AppStorage("persona.style") private var personaStyleRaw: String = PersonaStyle.casual.rawValue
    @AppStorage("persona.formality") private var personaFormalityRaw: String = Formality.polite.rawValue
    @AppStorage("persona.verbosity") private var personaVerbosityRaw: String = Verbosity.concise.rawValue
    @AppStorage("persona.emoji") private var personaEmoji: Bool = false
    @AppStorage("persona.instruction") private var personaInstruction: String = ""
    @AppStorage("persona.temperature") private var personaTemperature: Double = 0.3

    private var persona: PersonaSettings {
        get {
            PersonaSettings(
                style: PersonaStyle(rawValue: personaStyleRaw) ?? .casual,
                formality: Formality(rawValue: personaFormalityRaw) ?? .polite,
                verbosity: Verbosity(rawValue: personaVerbosityRaw) ?? .concise,
                emoji: personaEmoji
            )
        }
        set {
            personaStyleRaw = newValue.style.rawValue
            personaFormalityRaw = newValue.formality.rawValue
            personaVerbosityRaw = newValue.verbosity.rawValue
            personaEmoji = newValue.emoji
            personaInstruction = newValue.instruction
            personaTemperature = newValue.temperature ?? personaTemperature
        }
    }

    var body: some View {
        VStack {
            HStack {
                Text("会話ID: \(conversationId)").font(.footnote).foregroundColor(.secondary)
                Spacer()
            }.padding([.horizontal, .top])
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 10) {
                    ForEach(items) { m in
                        HStack {
                            if m.isMe { Spacer() }
                            VStack(alignment: .trailing, spacing: 2) {
                                Text(m.text)
                                    .padding(10)
                                    .background(m.isMe ? Color.blue.opacity(0.15) : Color.gray.opacity(0.15))
                                    .cornerRadius(10)
                                    .frame(maxWidth: .infinity, alignment: m.isMe ? .trailing : .leading)
                                if m.isMe && m.read {
                                    Text("既読").font(.caption2).foregroundColor(.secondary)
                                }
                            }
                            if !m.isMe { Spacer() }
                        }
                    }
                    if isTyping {
                        HStack {
                            Spacer()
                            Text("入力中…").font(.caption).foregroundColor(.secondary)
                        }
                    }
                }.padding()
            }
            HStack {
                TextField("メッセージ", text: $input)
                    .textFieldStyle(.roundedBorder)
                Button("送信") { Task { await sendStream() } }
                    .disabled(input.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            }.padding()
        }
        .onAppear { items = ChatStore.shared.load(conversationId: conversationId) }
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Button(action: { showPersonaSheet = true }) {
                    Image(systemName: "slider.horizontal.3")
                }
                .accessibilityLabel("ペルソナ設定")
            }
        }
        .sheet(isPresented: $showPersonaSheet) {
            PersonaSettingsView(
                style: $personaStyleRaw,
                formality: $personaFormalityRaw,
                verbosity: $personaVerbosityRaw,
                emoji: $personaEmoji,
                instruction: $personaInstruction,
                temperature: $personaTemperature
            )
        }
    }

    // Streaming send: progressively append deltas
    func sendStream() async {
        let text = input.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }
        input = ""
        items.append(Message(text: text, isMe: true, read: false))
        lastUserIndex = items.indices.last
        let startIndex = items.count
        var acc = ""
        do {
            isTyping = true
            var p = persona
            p.instruction = personaInstruction
            p.temperature = personaTemperature
            try await service.stream(userId: userId, conversationId: conversationId, message: text, persona: p, onDelta: { delta in
                acc += delta
                // update or append streaming bubble
                if items.count == startIndex {
                    items.append(Message(text: acc, isMe: false))
                } else {
                    items[items.count - 1] = Message(text: acc, isMe: false)
                }
                ChatStore.shared.save(conversationId: conversationId, messages: items)
            }, onDone: { final in
                isTyping = false
                if items.count == startIndex {
                    items.append(Message(text: final, isMe: false))
                } else {
                    items[items.count - 1] = Message(text: final, isMe: false)
                }
                if let idx = lastUserIndex, items.indices.contains(idx) {
                    items[idx].read = true
                }
                ChatStore.shared.save(conversationId: conversationId, messages: items)
            })
        } catch {
            items.append(Message(text: "ごめん、少し調子が悪いみたい。あとでもう一度試してくれる？", isMe: false))
            ChatStore.shared.save(conversationId: conversationId, messages: items)
            isTyping = false
        }
    }

    func send() async {
        let text = input.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }
        input = ""
        items.append(Message(text: text, isMe: true, read: false))
        lastUserIndex = items.indices.last
        ChatStore.shared.save(conversationId: conversationId, messages: items)
        do {
            var p = persona
            p.instruction = personaInstruction
            p.temperature = personaTemperature
            let reply = try await service.send(userId: userId, conversationId: conversationId, message: text, persona: p)
            items.append(Message(text: reply, isMe: false))
            if let idx = lastUserIndex, items.indices.contains(idx) {
                items[idx].read = true
            }
            ChatStore.shared.save(conversationId: conversationId, messages: items)
        } catch {
            items.append(Message(text: "ごめん、少し調子が悪いみたい。あとでもう一度試してくれる？", isMe: false))
            ChatStore.shared.save(conversationId: conversationId, messages: items)
        }
    }
}

private struct PersonaSettingsView: View {
    @Binding var style: String
    @Binding var formality: String
    @Binding var verbosity: String
    @Binding var emoji: Bool
    @Binding var instruction: String
    @Binding var temperature: Double

    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("スタイル")) {
                    Picker("スタイル", selection: $style) {
                        ForEach(PersonaStyle.allCases, id: \.rawValue) { s in
                            Text(s.label).tag(s.rawValue)
                        }
                    }
                }
                Section(header: Text("口調")) {
                    Picker("口調", selection: $formality) {
                        ForEach(Formality.allCases, id: \.rawValue) { f in
                            Text(f.label).tag(f.rawValue)
                        }
                    }
                    .pickerStyle(.segmented)
                }
                Section(header: Text("冗長さ")) {
                    Picker("冗長さ", selection: $verbosity) {
                        ForEach(Verbosity.allCases, id: \.rawValue) { v in
                            Text(v.label).tag(v.rawValue)
                        }
                    }
                    .pickerStyle(.segmented)
                }
                Section(header: Text("表現")) {
                    Toggle("絵文字を使う", isOn: $emoji)
                }
                Section(header: Text("カスタム指示 (任意)"), footer: Text("例: 『丁寧な日本語で、箇条書き中心、絵文字なし。』など自由に記述できます。")) {
                    ZStack(alignment: .topLeading) {
                        TextEditor(text: $instruction)
                            .frame(minHeight: 100)
                        if instruction.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                            Text("口調や役割などの追加指示を入力…")
                                .foregroundColor(.secondary)
                                .opacity(0.6)
                                .padding(.top, 8)
                                .padding(.leading, 5)
                        }
                    }
                    Button(role: .destructive) {
                        instruction = ""
                    } label: {
                        Label("クリア", systemImage: "xmark.circle")
                    }
                }
                Section(header: Text("創造性 (temperature)"), footer: Text("0=厳格/安定、1=自由/多様。")) {
                    HStack {
                        Slider(value: $temperature, in: 0...1, step: 0.05)
                        Text(String(format: "%.2f", temperature)).frame(width: 50, alignment: .trailing)
                    }
                }
            }
            .navigationTitle("ペルソナ設定")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("閉じる", action: { dismiss() }) }
                ToolbarItem(placement: .confirmationAction) { Button("OK", action: { dismiss() }) }
            }
            .toolbar {
                ToolbarItem(placement: .bottomBar) {
                    Button(role: .destructive) {
                        // デフォルトへ戻す
                        style = PersonaStyle.casual.rawValue
                        formality = Formality.polite.rawValue
                        verbosity = Verbosity.concise.rawValue
                        emoji = false
                        instruction = ""
                        temperature = 0.3
                    } label: {
                        Label("デフォルトに戻す", systemImage: "arrow.counterclockwise")
                    }
                }
            }
        }
    }
}
