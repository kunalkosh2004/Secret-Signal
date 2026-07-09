export interface ChatMessage {
  id: number
  user_id: number
  username: string
  content: string
  created_at: string
}

export interface ChatMessageSentEvent {
  type: 'MESSAGE_SENT'
  message: ChatMessage
}
