import type { ReactNode } from 'react'

export function MessageBubble({ sender, children }: { sender: 'user' | 'assistant'; children: ReactNode }) {
  const isUser = sender === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={[
          'max-w-2xl rounded-2xl px-4 py-3 shadow-lg',
          isUser ? 'bg-sky-600 text-white' : 'border border-slate-700 bg-slate-900 text-slate-100',
        ].join(' ')}
      >
        {children}
      </div>
    </div>
  )
}
