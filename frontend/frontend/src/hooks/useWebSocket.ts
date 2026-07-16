import { useEffect, useRef, useState, useCallback } from 'react'
import { useAuthStore } from '../stores/authStore'
import type {
  RoomStateEvent,
  WsClientEvent,
  WsServerEvent,
  RoleAssignmentEvent,
  PhaseChangedEvent,
} from '../features/room/types/room.types'
import type {
  GameStateEvent,
  GameStartEvent,
  GameOverEvent,
  MissionAssignmentEvent,
  MissionProgressEvent,
  VoteResultsEvent,
  VoteCastEvent,
  TimerUpdatedEvent,
  MLTrainedEvent,
  SignalAIResultEvent,
} from '../features/room/types/game.types'
import type { ChatMessage } from '../features/chat/types/chat.types'

function mergeChatMessages(previous: ChatMessage[], incoming: ChatMessage[]): ChatMessage[] {
  const messagesById = new Map<number, ChatMessage>()
  const optimisticMessages = previous.filter((message) => message.id < 0)

  for (const message of previous) {
    if (message.id >= 0) {
      messagesById.set(message.id, message)
    }
  }

  for (const message of incoming) {
    messagesById.set(message.id, message)
  }

  return [...messagesById.values(), ...optimisticMessages].sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
  )
}

interface UseWebSocketResult {
  isConnected: boolean
  lastRoomState: RoomStateEvent | null
  lastGameStart: GameStartEvent | null
  lastRoleAssignment: RoleAssignmentEvent | null
  lastPhaseChanged: PhaseChangedEvent | null
  lastGameState: GameStateEvent | null
  lastGameOver: GameOverEvent | null
  lastMissionAssignment: MissionAssignmentEvent | null
  lastMissionProgress: MissionProgressEvent | null
  lastVoteResults: VoteResultsEvent | null
  lastVoteCast: VoteCastEvent | null
  lastTimerUpdated: TimerUpdatedEvent | null
  lastMLTrained: MLTrainedEvent | null
  lastSignalAIResult: SignalAIResultEvent | null
  chatMessages: ChatMessage[]
  sendMessage: (event: WsClientEvent) => void
}

export function useWebSocket(roomCode: string | null): UseWebSocketResult {
  const [isConnected, setIsConnected] = useState(false)
  const [lastRoomState, setLastRoomState] = useState<RoomStateEvent | null>(null)
  const [lastGameStart, setLastGameStart] = useState<GameStartEvent | null>(null)
  const [lastRoleAssignment, setLastRoleAssignment] = useState<RoleAssignmentEvent | null>(null)
  const [lastPhaseChanged, setLastPhaseChanged] = useState<PhaseChangedEvent | null>(null)
  const [lastGameState, setLastGameState] = useState<GameStateEvent | null>(null)
  const [lastGameOver, setLastGameOver] = useState<GameOverEvent | null>(null)
  const [lastMissionAssignment, setLastMissionAssignment] = useState<MissionAssignmentEvent | null>(null)
  const [lastMissionProgress, setLastMissionProgress] = useState<MissionProgressEvent | null>(null)
  const [lastVoteResults, setLastVoteResults] = useState<VoteResultsEvent | null>(null)
  const [lastVoteCast, setLastVoteCast] = useState<VoteCastEvent | null>(null)
  const [lastTimerUpdated, setLastTimerUpdated] = useState<TimerUpdatedEvent | null>(null)
  const [lastMLTrained, setLastMLTrained] = useState<MLTrainedEvent | null>(null)
  const [lastSignalAIResult, setLastSignalAIResult] = useState<SignalAIResultEvent | null>(null)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const wsRef = useRef<WebSocket | null>(null)
  const tokenRef = useRef<string | null>(null)

  useEffect(() => {
    const unsub = useAuthStore.subscribe((state) => {
      tokenRef.current = state.token
    })
    tokenRef.current = useAuthStore.getState().token
    return unsub
  }, [])

  const sendMessage = useCallback((event: WsClientEvent) => {
    // Optimistic local update for chat messages
    if (event.type === 'SEND_MESSAGE') {
      const state = useAuthStore.getState()
      if (state.user) {
        const optimistic: ChatMessage = {
          id: -Date.now(),
          user_id: state.user.id,
          username: state.user.username,
          content: event.content,
          reply_to_message_id: (event as any).reply_to_message_id ?? null,
          reactions: {},
          created_at: new Date().toISOString(),
        }
        setChatMessages((prev) => [...prev, optimistic])
      }
    }
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(event))
    }
  }, [])

  useEffect(() => {
    if (!roomCode) {
      setIsConnected(false)
      setLastRoomState(null)
      setLastGameStart(null)
      setLastRoleAssignment(null)
      setLastPhaseChanged(null)
      setLastGameState(null)
      setLastGameOver(null)
      setLastMissionAssignment(null)
      setLastMissionProgress(null)
      setLastVoteResults(null)
      setLastVoteCast(null)
      setLastTimerUpdated(null)
      setLastMLTrained(null)
      setLastSignalAIResult(null)
      setChatMessages([])
      return
    }

    const token = tokenRef.current
    if (!token) return

    let reconnectTimer: ReturnType<typeof setTimeout> | null = null
    let closed = false

    function connect() {
      if (closed) return
      const currentToken = tokenRef.current
      if (!currentToken) return

      const isSecure = window.location.protocol === 'https:'
      const wsProtocol = isSecure ? 'wss:' : 'ws:'
      const wsHost = window.location.host
      const url = `${wsProtocol}//${wsHost}/ws?token=${currentToken}&room_code=${roomCode}`
      const ws = new WebSocket(url)
      wsRef.current = ws
      ws.onopen = () => {
        setIsConnected(true)
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as WsServerEvent
          switch (data.type) {
            case 'ROOM_STATE':
              setLastRoomState(data)
              break
            case 'GAME_START':
              setLastGameStart(data)
              break
            case 'ROLE_ASSIGNMENT':
              setLastRoleAssignment(data)
              break
            case 'PHASE_CHANGED':
              setLastPhaseChanged(data)
              break
            case 'GAME_STATE':
              setLastGameState(data)
              break
            case 'GAME_OVER':
              setLastGameOver(data)
              break
            case 'MISSION_ASSIGNMENT':
              setLastMissionAssignment(data)
              break
            case 'MISSION_PROGRESS':
              setLastMissionProgress(data)
              break
            case 'VOTE_RESULTS':
              setLastVoteResults(data)
              break
            case 'VOTE_CAST':
              setLastVoteCast(data)
              break
            case 'TIMER_UPDATED':
              setLastTimerUpdated(data)
              break
            case 'ML_TRAINED':
              setLastMLTrained(data)
              break
            case 'SIGNAL_AI_RESULT':
              setLastSignalAIResult(data)
              break
            case 'CHAT_HISTORY':
              setChatMessages((prev) => mergeChatMessages(prev, data.messages))
              break
            case 'MESSAGE_SENT':
              setChatMessages((prev) => {
                const idx = prev.findIndex(
                  (m) => m.id < 0 && m.user_id === data.message.user_id && m.content === data.message.content,
                )
                if (idx !== -1) {
                  const next = [...prev]
                  next[idx] = data.message
                  return next
                }
                return mergeChatMessages(prev, [data.message])
              })
              break
            case 'REACTION_ADDED':
            case 'REACTION_REMOVED':
              setChatMessages((prev) =>
                prev.map((m) =>
                  m.id === data.message_id
                    ? { ...m, reactions: data.reactions }
                    : m,
                ),
              )
              break
          }
        } catch {
          // ignore malformed messages
        }
      }

      ws.onclose = () => {
        setIsConnected(false)
        wsRef.current = null
        if (!closed && tokenRef.current && tokenRef.current === currentToken) {
          reconnectTimer = setTimeout(connect, 2000)
        }
      }

      ws.onerror = () => {
        if (ws.readyState === WebSocket.OPEN) ws.close()
      }
    }

    connect()

    return () => {
      closed = true
      if (reconnectTimer) clearTimeout(reconnectTimer)
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close()
      }
      wsRef.current = null
      setIsConnected(false)
    }
  }, [roomCode])

  return {
    isConnected,
    lastRoomState,
    lastGameStart,
    lastRoleAssignment,
    lastPhaseChanged,
    lastGameState,
    lastGameOver,
    lastMissionAssignment,
    lastMissionProgress,
    lastVoteResults,
    lastVoteCast,
    lastTimerUpdated,
    lastMLTrained,
    lastSignalAIResult,
    chatMessages,
    sendMessage,
  }
}
