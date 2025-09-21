# サーバ側のペルソナ対応ガイド

iOS クライアントから送られるペルソナ設定をサーバで受け取り、プロンプトに反映するための実装ガイドです。Express/Next.js どちらでも同様に扱えます。

## 受け取るパラメータ

POST `/api/chat`（JSON body）

- `userId: string`
- `conversationId: string`
- `message: string`
- `persona: { style, formality, verbosity, emoji, instruction? }`
- `temperature?: number`（0.0〜1.0）

GET `/api/chat/stream`（query）

- `userId, conversationId, message`
- `personaStyle, personaFormality, personaVerbosity, personaEmoji(1|0), personaInstruction?`
- `temperature?`

## サニタイズ & 既定値

```ts
type Persona = {
  style: 'business' | 'casual' | 'teacher' | 'brainstorm'
  formality: 'polite' | 'casual'
  verbosity: 'concise' | 'detailed'
  emoji: boolean
  instruction?: string
}

const DEFAULT_PERSONA: Persona = {
  style: 'casual',
  formality: 'polite',
  verbosity: 'concise',
  emoji: false
}

function clampTemp(x: any, fallback = 0.3) {
  const n = Number(x)
  if (Number.isFinite(n)) return Math.min(1, Math.max(0, n))
  return fallback
}

function sanitizePersona(raw: any): Persona {
  const p = { ...DEFAULT_PERSONA, ...(raw || {}) }
  if (!['business','casual','teacher','brainstorm'].includes(p.style)) p.style = DEFAULT_PERSONA.style
  if (!['polite','casual'].includes(p.formality)) p.formality = DEFAULT_PERSONA.formality
  if (!['concise','detailed'].includes(p.verbosity)) p.verbosity = DEFAULT_PERSONA.verbosity
  p.emoji = !!p.emoji
  if (typeof p.instruction === 'string') {
    // 長過ぎる自由指示は切り詰め
    p.instruction = p.instruction.slice(0, 600)
  } else {
    delete p.instruction
  }
  return p
}
```

## システムプロンプトの生成

```ts
function personaToSystemPrompt(p: Persona) {
  const tone = {
    business: 'ビジネス的に、簡潔で要点重視',
    casual: 'フレンドリーで親しみやすく',
    teacher: '丁寧に、段階的に解説',
    brainstorm: '発散的に複数案を提示'
  }[p.style]

  const politeness = p.formality === 'polite'
    ? '敬体（です・ます）で話す'
    : 'カジュアルな常体（〜だ・〜する）で話す'

  const length = p.verbosity === 'concise'
    ? '回答は簡潔に。箇条書き中心、3〜5項目を目安。'
    : '必要に応じて詳しく。段落・箇条書きを使い分ける。'

  const emoji = p.emoji
    ? '絵文字の使用は可。ただし過剰にしない。'
    : '絵文字や顔文字は使用しない。'

  const custom = p.instruction ? `\n- 追加指示: ${p.instruction}` : ''

  return [
    'You are a helpful assistant for Japanese users.',
    '- Language: Japanese',
    `- Tone/Style: ${tone}`,
    `- Politeness: ${politeness}`,
    `- Verbosity: ${length}`,
    `- Emoji: ${emoji}`,
    '- 禁止: ハルシネーションを避け、不明点は率直に不明と伝える。',
    custom
  ].join('\n')
}
```

## Express（POST /api/chat）実装例

```ts
import express from 'express'
import OpenAI from 'openai'

const app = express()
app.use(express.json())

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY })

app.post('/api/chat', async (req, res) => {
  try {
    const { userId, conversationId, message, persona, temperature } = req.body || {}
    const p = sanitizePersona(persona)
    const sys = personaToSystemPrompt(p)
    const temp = clampTemp(temperature, 0.3)

    const r = await openai.chat.completions.create({
      model: process.env.OPENAI_MODEL || 'gpt-4o-mini',
      temperature: temp,
      messages: [
        { role: 'system', content: sys },
        { role: 'user', content: message }
      ]
    })

    const reply = r.choices?.[0]?.message?.content || ''
    res.json({ reply })
  } catch (e) {
    console.error(e)
    res.status(500).json({ error: 'server_error' })
  }
})
```

## Express（SSE /api/chat/stream）実装例

```ts
app.get('/api/chat/stream', async (req, res) => {
  try {
    res.setHeader('Content-Type', 'text/event-stream')
    res.setHeader('Cache-Control', 'no-cache')
    res.setHeader('Connection', 'keep-alive')

    const p = sanitizePersona({
      style: req.query.personaStyle,
      formality: req.query.personaFormality,
      verbosity: req.query.personaVerbosity,
      emoji: req.query.personaEmoji === '1',
      instruction: req.query.personaInstruction
    })
    const sys = personaToSystemPrompt(p)
    const temp = clampTemp(req.query.temperature, 0.3)
    const message = String(req.query.message || '')

    const stream = await openai.chat.completions.create({
      model: process.env.OPENAI_MODEL || 'gpt-4o-mini',
      temperature: temp,
      messages: [
        { role: 'system', content: sys },
        { role: 'user', content: message }
      ],
      stream: true
    })

    for await (const chunk of stream) {
      const delta = chunk.choices?.[0]?.delta?.content || ''
      if (delta) {
        res.write(`event: delta\n`)
        res.write(`data: ${JSON.stringify({ delta })}\n\n`)
      }
    }
    // 最終確定（任意で全文を返したい場合）
    // res.write(`event: done\n`)
    // res.write(`data: ${JSON.stringify({ final })}\n\n`)
    res.end()
  } catch (e) {
    console.error(e)
    try { res.end() } catch {}
  }
})
```

> Anthropicや他プロバイダを使う場合も、`sys` を system プロンプト、`temp` を温度に渡す点は同じです。Streaming の for-await で `delta` を取り出して `event: delta` で転送してください。

## 既存の環境変数との整合

- 既存の `REPLY_FLEX` / `ROMANCE_LEVEL` / `PERSONA_STYLE` などのサーバ側既定は、「UIからの指定があればそれを優先し、なければ既定を使う」方針にします。
- セキュリティ上、`instruction` は長さやNGワードで制限可能です（最大600〜1000字程度、HTML/URL除去など）。

## 確認チェックリスト

- [ ] UI からの `persona*` / `temperature` がサーバで受理される
- [ ] サニタイズ後の system プロンプトが意図したトーンになる
- [ ] POST と SSE の双方で反映される
- [ ] サーバのデフォルト設定と競合しない（UI指定が優先）

