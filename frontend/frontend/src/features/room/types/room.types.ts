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
  is_ready?: boolean
}

export interface RoomStateEvent {
  type: 'ROOM_STATE'
  room: RoomResponse
  players: RoomPlayer[]
}

export interface GameStartEvent {
  type: 'GAME_START'
  game_id: number
}

export interface RoleAssignmentEvent {
  type: 'ROLE_ASSIGNMENT'
  game_id: number
  role: string
}

export interface PhaseChangedEvent {
  type: 'PHASE_CHANGED'
  game_id: number
  status: string
  round_number: number
  phase: string
}

import type { GameStateEvent } from './game.types'
import type { ChatMessageSentEvent } from '../../chat/types/chat.types'

export type WsServerEvent =
  | RoomStateEvent
  | GameStartEvent
  | RoleAssignmentEvent
  | PhaseChangedEvent
  | GameStateEvent
  | ChatMessageSentEvent

export type WsClientEvent =
  | { type: 'PLAYER_READY'; payload: { ready: boolean } }
  | { type: 'SEND_MESSAGE'; content: string }
  | { type: 'LEAVE_ROOM' }
