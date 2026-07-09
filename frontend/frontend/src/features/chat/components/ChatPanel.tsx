import { useState, useRef, useEffect } from 'react'
import type { ChatMessage } from '../types/chat.types'

interface ChatPanelProps {
  messages: ChatMessage[]
  onSend: (content: string) => void
  currentUserId: number
}

export function ChatPanel({ messages, onSend, currentUserId }: ChatPanelProps) {
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = input.trim()
    if (!trimmed) return
    onSend(trimmed)
    setInput('')
  }

  return (
    <div className="flex flex-col h-full border border-gray-400/30 rounded overflow-hidden bg-gray-100/50">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {messages.map((msg) => {
          const isMe = msg.user_id === currentUserId
          return (
            <div
              key={msg.id}
              className={`flex ${isMe ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[75%] px-3 py-2 rounded text-xs font-mono leading-relaxed ${
                  isMe
                    ? 'bg-accent/15 text-gray-900 border border-accent/20'
                    : 'bg-gray-200 text-gray-700 border border-gray-400/20'
                }`}
              >
                {!isMe && (
                  <div className="text-[10px] font-mono text-gray-500 mb-0.5">
                    {msg.username}
                  </div>
                )}
                <div>{msg.content}</div>
              </div>
            </div>
          )
        })}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form
        onSubmit={handleSubmit}
        className="border-t border-gray-400/20 flex items-stretch"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message..."
          className="flex-1 bg-gray-100 px-3 py-2.5 text-xs font-mono text-gray-900 placeholder-gray-500 outline-none border-r border-gray-400/20"
        />
        <button
          type="submit"
          disabled={!input.trim()}
          className="px-4 py-2.5 text-xs font-mono tracking-wider text-gray-600 hover:text-gray-900 hover:bg-gray-200 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          SEND
        </button>
      </form>
    </div>
  )
}
