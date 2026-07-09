export interface GameStateEvent {
  type: 'GAME_STATE'
  game_id: number
  status: string
  round_number: number
  phase: string
}
