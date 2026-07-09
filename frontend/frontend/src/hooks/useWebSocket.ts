import { useEffect, useRef, useState, useCallback } from 'react'
import { useAuthStore } from '../stores/authStore'
import type { RoomStateEvent, WsClientEvent } from '../features/room/types/room.types'

interface UseWebSocketResult {
  isConnected: boolean
  lastRoomState: RoomStateEvent | null
  sendMessage: (event: WsClientEvent) => void
}

export function useWebSocket(roomCode: string | null): UseWebSocketResult {
  const [isConnected, setIsConnected] = useState(false)
  const [lastRoomState, setLastRoomState] = useState<RoomStateEvent | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const tokenRef = useRef<string | null>(null)

  // Keep token ref updated without re-triggering the effect
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
          const data = JSON.parse(event.data) as RoomStateEvent
          if (data.type === 'ROOM_STATE') {
            setLastRoomState(data)
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

  return { isConnected, lastRoomState, sendMessage }
}
