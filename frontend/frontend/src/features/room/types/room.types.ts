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

export interface RoleAssignmentEvent {
  type: 'ROLE_ASSIGNMENT'
  game_id: number
  role: string
}

export interface PhaseChangedEvent {
  type: 'PHASE_CHANGED'
  game: {
    id: number
    status: string
    round_number: number
    phase: string
  }
}

import type {
  GameStateEvent,
  GameStartEvent,
  GameOverEvent,
  MissionAssignmentEvent,
  MissionProgressEvent,
  VoteResultsEvent,
  VoteCastEvent,
} from './game.types'
import type {
  ChatHistoryEvent,
  ChatMessageSentEvent,
} from '../../chat/types/chat.types'

export type WsServerEvent =
  | RoomStateEvent
  | GameStartEvent
  | RoleAssignmentEvent
  | PhaseChangedEvent
  | GameStateEvent
  | GameOverEvent
  | MissionAssignmentEvent
  | MissionProgressEvent
  | VoteResultsEvent
  | VoteCastEvent
  | ChatMessageSentEvent
  | ChatHistoryEvent

export type WsClientEvent =
  | { type: 'PLAYER_READY'; payload: { ready: boolean } }
  | { type: 'SEND_MESSAGE'; content: string }
  | { type: 'LEAVE_ROOM' }
  | { type: 'CAST_VOTE'; payload: { target_user_id: number } }
