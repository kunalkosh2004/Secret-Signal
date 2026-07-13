export interface GameStateEvent {
  type: 'GAME_STATE'
  game: {
    id: number
    status: string
    round_number: number
    phase: string
  }
}

export interface GameStartEvent {
  type: 'GAME_START'
  game: {
    id: number
    room_id: number
    status: string
    round_number: number
    phase: string
  }
}

export interface GameOverEvent {
  type: 'GAME_OVER'
  game: {
    id: number
    status: string
    round_number: number
    phase: string
  }
  winner: string
  reason: string
  scores?: GameScore[]
}

export interface GameScore {
  user_id: number
  username: string
  role: string
  score: number
}

export interface MissionAssignmentEvent {
  type: 'MISSION_ASSIGNMENT'
  game_id: number
  missions: MissionData[]
}

export interface MissionData {
  id: number
  mission_type: string
  title: string
  description: string
  target_value: number
  current_value: number
  status: string
  round_number: number
}

export interface MissionProgressEvent {
  type: 'MISSION_PROGRESS'
  mission: {
    id: number
    current_value: number
    target_value: number
    status: string
  }
}

export interface VoteTally {
  target_user_id: number
  count: number
}

export interface VoteResults {
  round_number: number
  total_votes: number
  tallies: VoteTally[]
  coordinator_identified: boolean
  coordinator_user_id: number | null
}

export interface VoteResultsEvent {
  type: 'VOTE_RESULTS'
  results: VoteResults
}

export interface VoteCastEvent {
  type: 'VOTE_CAST'
  target_user_id: number
}

export interface TimerUpdatedEvent {
  type: 'TIMER_UPDATED'
  phase: string
  duration_seconds: number
  ends_at: string
}

export interface MLTrainedEvent {
  type: 'ML_TRAINED'
  accuracy: number | null
  samples_used: number | null
}
