export interface ReplayPlayer {
  user_id: number
  username: string
  role: string
  score: number
}

export interface ReplayEvent {
  sequence_number: number
  event_type: string
  actor_id: number | null
  actor_name: string | null
  round_number: number | null
  payload: Record<string, unknown>
  metadata: Record<string, unknown>
  timestamp: string
  relative_time_seconds: number
  label: string
  category: string
}

export interface ReplayGameInfo {
  game_id: number
  room_code: string
  status: string
  max_rounds: number
  total_events: number
  started_at: string | null
  ended_at: string | null
  players: ReplayPlayer[]
  winner: string | null
  reason: string | null
}

export interface ReplayTimeline {
  game: ReplayGameInfo
  events: ReplayEvent[]
  total_events: number
  total_rounds: number
  duration_seconds: number
}

export interface ReplayStateSnapshot {
  sequence_number: number
  round_number: number
  phase: string
  players: ReplayPlayer[]
  messages_sent: number
  votes_cast: number
  missions_active: number
  missions_completed: number
}

export const EVENT_CATEGORY_COLORS: Record<string, string> = {
  game_start: 'bg-green-500',
  game_end: 'bg-red-500',
  round_start: 'bg-blue-500',
  round_end: 'bg-blue-400',
  phase: 'bg-purple-500',
  role: 'bg-yellow-500',
  message: 'bg-gray-400',
  reaction: 'bg-pink-400',
  mission: 'bg-orange-500',
  vote: 'bg-red-400',
  player: 'bg-cyan-500',
  other: 'bg-gray-300',
}

export const EVENT_CATEGORY_ICONS: Record<string, string> = {
  game_start: '\u25B6',
  game_end: '\u25A0',
  round_start: '\u21BB',
  round_end: '\u21BA',
  phase: '\u2B50',
  role: '\u{1F3AD}',
  message: '\u{1F4AC}',
  reaction: '\u{1F44D}',
  mission: '\u{1F3AF}',
  vote: '\u{1F5F3}',
  player: '\u{1F464}',
  other: '\u2022',
}
