import { useEffect, useRef, useState, useCallback } from 'react'
import { useAuthStore } from '../stores/authStore'
import type {
  RoomStateEvent,
  WsClientEvent,
  WsServerEvent,
  GameStartEvent,
  RoleAssignmentEvent,
  PhaseChangedEvent,
} from '../features/room/types/room.types'
import type { GameStateEvent } from '../features/room/types/game.types'
import type { ChatMessage } from '../features/chat/types/chat.types'

interface UseWebSocketResult {
  isConnected: boolean
  lastRoomState: RoomStateEvent | null
  lastGameStart: GameStartEvent | null
  lastRoleAssignment: RoleAssignmentEvent | null
  lastPhaseChanged: PhaseChangedEvent | null
  lastGameState: GameStateEvent | null
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
      setChatMessages([])
      return
    }

    const token = tokenRef.current
    if (!token) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${protocol}//${window.location.host}/ws?token=${token}&room_code=${roomCode}`

    function connect() {
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
            case 'MESSAGE_SENT':
              setChatMessages((prev) => [...prev, data.message])
              break
          }
        } catch {
          // ignore malformed messages
        }
      }

      ws.onclose = () => {
        setIsConnected(false)
        wsRef.current = null
      }

      ws.onerror = () => {
        ws.close()
      }
    }

    connect()

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
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
    chatMessages,
    sendMessage,
  }
}
