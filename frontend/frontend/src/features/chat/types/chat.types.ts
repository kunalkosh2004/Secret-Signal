export interface ReactionCount {
  count: number
  user_ids: number[]
}

export interface ChatMessage {
  id: number
  user_id: number
  username: string
  content: string
  reply_to_message_id: number | null
  reactions: Record<string, ReactionCount>
  created_at: string
}

export interface ChatMessageSentEvent {
  type: 'MESSAGE_SENT'
  message: ChatMessage
}

export interface ChatHistoryEvent {
  type: 'CHAT_HISTORY'
  messages: ChatMessage[]
}

export interface ReactionAddedEvent {
  type: 'REACTION_ADDED'
  message_id: number
  user_id: number
  emoji: string
  reactions: Record<string, ReactionCount>
}

export interface ReactionRemovedEvent {
  type: 'REACTION_REMOVED'
  message_id: number
  user_id: number
  emoji: string
  reactions: Record<string, ReactionCount>
}
