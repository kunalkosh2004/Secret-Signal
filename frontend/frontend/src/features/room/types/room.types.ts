export interface CreateRoomRequest {
  max_players: number
  settings: Record<string, unknown>
}

export interface JoinRoomRequest {
  code: string
}

export interface RoomResponse {
  id: number
  code: string
  host_id: number
  status: string
  max_players: number
  settings: Record<string, unknown>
  created_at: string
}

export interface RoomPlayer {
  id: number
  username: string
}

export interface RoomStateEvent {
  type: 'ROOM_STATE'
  room: RoomResponse
  players: RoomPlayer[]
}

export type WsClientEvent =
  | { type: 'PLAYER_READY' }
  | { type: 'SEND_MESSAGE'; content: string }
  | { type: 'LEAVE_ROOM' }
