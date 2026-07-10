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
} from '../features/room/types/game.types'
import type { ChatMessage } from '../features/chat/types/chat.types'

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
      setChatMessages([])
      return
    }

    const token = tokenRef.current
    if (!token) return

    const url = `ws://localhost:8000/ws?token=${token}&room_code=${roomCode}`

    let reconnectTimer: ReturnType<typeof setTimeout> | null = null
    let closed = false

    function connect() {
      if (closed) return
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
            case 'MESSAGE_SENT':
              setChatMessages((prev) => {
                // Replace optimistic message with real one from server
                const idx = prev.findIndex(
                  (m) => m.id < 0 && m.user_id === data.message.user_id && m.content === data.message.content,
                )
                if (idx !== -1) {
                  const next = [...prev]
                  next[idx] = data.message
                  return next
                }
                return [...prev, data.message]
              })
              break
          }
        } catch {
          // ignore malformed messages
        }
      }

      ws.onclose = () => {
        setIsConnected(false)
        wsRef.current = null
        if (!closed) {
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
    chatMessages,
    sendMessage,
  }
}
