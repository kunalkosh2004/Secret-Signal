export interface PlayerAnalysis {
  user_id: number
  role: string
  message_count: number
  questions_asked: number
  topic_initiations: number
  avg_message_length: number
  suspicion_score: number
  voting_accuracy: number
  round_breakdown: RoundBreakdown[]
}

export interface RoundBreakdown {
  round: number
  message_count: number
  questions: number
}

export interface GameAnalysis {
  game_id: number
  total_rounds: number
  completed_missions: number
  winner: string
  summary: string
  coordination_score: number
  voting_patterns: Record<string, Record<number, number>>
  players: PlayerAnalysis[]
}
