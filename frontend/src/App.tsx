import { FormEvent, useEffect, useRef, useState } from 'react'
import { askQuestion, ingestFolder, type AskResponse } from './api'
import { MessageBubble } from './components/MessageBubble'
import { SourceCitation } from './components/SourceCitation'

type ChatMessage = {
  sender: 'user' | 'assistant'
  text: string
  sources?: AskResponse['sources']
  grounded?: boolean
}

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      sender: 'assistant',
      text: 'Ask a question about the internal docs. I will answer only from the indexed documents.',
      grounded: true,
    },
  ])
  const [question, setQuestion] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const hasIngestedRef = useRef(false)

  useEffect(() => {
    if (hasIngestedRef.current) {
      return
    }
    hasIngestedRef.current = true

    void ingestFolder().catch(() => {
      setMessages((current) => [
        ...current,
        {
          sender: 'assistant',
          text: 'The backend is not reachable. Make sure the API service is running.',
          grounded: false,
        },
      ])
    })
  }, [])

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    const trimmed = question.trim()
    if (!trimmed || isLoading) {
      return
    }

    setMessages((current) => [...current, { sender: 'user', text: trimmed }])
    setQuestion('')
    setIsLoading(true)

    try {
      const response = await askQuestion(trimmed)
      setMessages((current) => [
        ...current,
        {
          sender: 'assistant',
          text: response.answer,
          sources: response.sources,
          grounded: response.grounded,
        },
      ])
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          sender: 'assistant',
          text: error instanceof Error ? error.message : 'Something went wrong.',
          grounded: false,
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto flex max-w-5xl flex-col gap-6 px-4 py-8">
        <header className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-2xl">
          <p className="text-xs uppercase tracking-[0.2em] text-sky-300">Knowledge Base</p>
          <h1 className="mt-2 text-3xl font-semibold">Internal Docs Q&A Assistant</h1>
        </header>

        <main className="flex min-h-[600px] flex-col rounded-2xl border border-slate-800 bg-slate-900/70 p-4 shadow-2xl">
          <div className="flex-1 space-y-4 overflow-y-auto p-2">
            {messages.map((message, index) => (
              <div key={`${message.sender}-${index}`} className="space-y-2">
                <MessageBubble sender={message.sender}>
                  <p className="whitespace-pre-wrap">{message.text}</p>
                </MessageBubble>

                {message.sender === 'assistant' && message.sources && message.sources.length > 0 ? (
                  <div className="ml-4 space-y-2">
                    {message.sources.map((source, sourceIndex) => (
                      <SourceCitation key={`${source.filename}-${sourceIndex}`} source={source} />
                    ))}
                  </div>
                ) : null}

                {message.sender === 'assistant' && message.grounded === false ? (
                  <div className="ml-4 rounded-xl border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-sm text-amber-100">
                    Not found in the documents.
                  </div>
                ) : null}
              </div>
            ))}

            {isLoading ? (
              <div className="flex justify-start">
                <div className="rounded-2xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-slate-300">
                  Thinking…
                </div>
              </div>
            ) : null}
          </div>

          <form onSubmit={handleSubmit} className="mt-4 flex gap-3 border-t border-slate-800 pt-4">
            <input
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Ask a question about the docs"
              className="flex-1 rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 outline-none transition focus:border-sky-500"
            />
            <button
              type="submit"
              disabled={isLoading}
              className="rounded-xl bg-sky-600 px-5 py-3 font-medium text-white transition hover:bg-sky-500 disabled:cursor-not-allowed disabled:bg-slate-700"
            >
              Send
            </button>
          </form>
        </main>
      </div>
    </div>
  )
}
