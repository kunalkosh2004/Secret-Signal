import { useState, useRef, useEffect } from 'react'
import type { ChatMessage } from '../types/chat.types'

const QUICK_EMOJIS = ['👍', '👎', '❤️', '😂', '😮', '😢', '🔥', '👀', '🎯', '✅']

interface ChatPanelProps {
  messages: ChatMessage[]
  onSend: (content: string, replyToMessageId?: number | null) => void
  onReact?: (messageId: number, emoji: string) => void
  onRemoveReaction?: (messageId: number, emoji: string) => void
  currentUserId: number
}

export function ChatPanel({ messages, onSend, onReact, onRemoveReaction, currentUserId }: ChatPanelProps) {
  const [input, setInput] = useState('')
  const [replyTo, setReplyTo] = useState<ChatMessage | null>(null)
  const [emojiPickerMessageId, setEmojiPickerMessageId] = useState<number | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Close emoji picker on outside click
  useEffect(() => {
    const handleClick = () => setEmojiPickerMessageId(null)
    if (emojiPickerMessageId !== null) {
      document.addEventListener('click', handleClick)
      return () => document.removeEventListener('click', handleClick)
    }
  }, [emojiPickerMessageId])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = input.trim()
    if (!trimmed) return
    onSend(trimmed, replyTo?.id ?? null)
    setInput('')
    setReplyTo(null)
  }

  const handleReply = (msg: ChatMessage) => {
    setReplyTo(msg)
    inputRef.current?.focus()
  }

  const handleCancelReply = () => {
    setReplyTo(null)
  }

  const handleEmojiPickerToggle = (e: React.MouseEvent, messageId: number) => {
    e.stopPropagation()
    setEmojiPickerMessageId(emojiPickerMessageId === messageId ? null : messageId)
  }

  const handleEmojiSelect = (messageId: number, emoji: string) => {
    const msg = messages.find((m) => m.id === messageId)
    if (!msg || !onReact || !onRemoveReaction) return

    const reaction = msg.reactions[emoji]
    const hasReacted = reaction?.user_ids.includes(currentUserId)

    if (hasReacted) {
      onRemoveReaction(messageId, emoji)
    } else {
      onReact(messageId, emoji)
    }
    setEmojiPickerMessageId(null)
  }

  const messageMap = new Map(messages.map((m) => [m.id, m]))

  return (
    <div className="flex flex-col h-full border border-gray-400/30 rounded overflow-hidden bg-gray-100/50">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {messages.map((msg) => {
          const isMe = msg.user_id === currentUserId
          const repliedMessage = msg.reply_to_message_id ? messageMap.get(msg.reply_to_message_id) : null
          const reactions = msg.reactions ?? {}
          const reactionEntries = Object.entries(reactions)

          return (
            <div
              key={msg.id}
              className={`flex ${isMe ? 'justify-end' : 'justify-start'} group`}
            >
              <div
                className={`max-w-[75%] px-3 py-2 rounded text-xs font-mono leading-relaxed ${
                  isMe
                    ? 'bg-accent/15 text-gray-900 border border-accent/20'
                    : 'bg-gray-200 text-gray-700 border border-gray-400/20'
                }`}
              >
                <div className="flex items-center gap-2 text-[10px] font-mono text-gray-500 mb-0.5">
                  <span>{msg.username}</span>
                  <span className="opacity-50">
                    {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>

                {/* Reply preview */}
                {repliedMessage && (
                  <div className={`mb-1 pl-2 border-l-2 text-[10px] ${
                    isMe ? 'border-accent/40 text-accent/70' : 'border-gray-400/40 text-gray-500'
                  }`}>
                    <span className="font-bold">@{repliedMessage.username}</span>
                    <span className="ml-1 opacity-70">{repliedMessage.content.slice(0, 50)}{repliedMessage.content.length > 50 ? '...' : ''}</span>
                  </div>
                )}

                <div>{msg.content}</div>

                {/* Reactions display */}
                {reactionEntries.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-1.5">
                    {reactionEntries.map(([emoji, data]) => {
                      const hasReacted = data.user_ids.includes(currentUserId)
                      return (
                        <button
                          key={emoji}
                          onClick={(e) => { e.stopPropagation(); handleEmojiSelect(msg.id, emoji) }}
                          className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-mono border transition-colors ${
                            hasReacted
                              ? 'bg-accent/15 border-accent/30 text-accent'
                              : 'bg-gray-100 border-gray-400/20 text-gray-600 hover:bg-gray-200'
                          }`}
                        >
                          <span>{emoji}</span>
                          <span>{data.count}</span>
                        </button>
                      )
                    })}
                  </div>
                )}

                {/* Action buttons — visible on hover */}
                <div className="flex items-center gap-2 mt-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  {!isMe && (
                    <button
                      onClick={() => handleReply(msg)}
                      className="text-[9px] font-mono text-gray-500 hover:text-accent transition-colors"
                    >
                      REPLY
                    </button>
                  )}
                  {onReact && (
                    <div className="relative">
                      <button
                        onClick={(e) => handleEmojiPickerToggle(e, msg.id)}
                        className="text-[9px] font-mono text-gray-500 hover:text-accent transition-colors"
                      >
                        REACT
                      </button>
                      {/* Emoji picker dropdown */}
                      {emojiPickerMessageId === msg.id && (
                        <div
                          className="absolute bottom-full left-0 mb-1 bg-white border border-gray-400/30 rounded shadow-lg p-1.5 flex gap-1 z-50"
                          onClick={(e) => e.stopPropagation()}
                        >
                          {QUICK_EMOJIS.map((emoji) => (
                            <button
                              key={emoji}
                              onClick={() => handleEmojiSelect(msg.id, emoji)}
                              className="w-7 h-7 flex items-center justify-center rounded hover:bg-gray-100 transition-colors text-sm"
                            >
                              {emoji}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )
        })}
        <div ref={bottomRef} />
      </div>

      {/* Reply preview bar */}
      {replyTo && (
        <div className="border-t border-accent/20 bg-accent/5 px-3 py-1.5 flex items-center justify-between">
          <div className="text-[10px] font-mono text-accent/70 truncate">
            Replying to <span className="font-bold">@{replyTo.username}</span>: {replyTo.content.slice(0, 40)}...
          </div>
          <button
            onClick={handleCancelReply}
            className="text-[10px] font-mono text-gray-500 hover:text-red-500 ml-2"
          >
            ✕
          </button>
        </div>
      )}

      {/* Input */}
      <form
        onSubmit={handleSubmit}
        className="border-t border-gray-400/20 flex items-stretch"
      >
        <input
          ref={inputRef}
          type="text"
          id="chat-input"
          name="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={replyTo ? `Reply to @${replyTo.username}...` : 'Type a message...'}
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
