export type ServiceStatus = 'healthy' | 'degraded' | 'down' | 'unknown'

export type LogLevel = 'INFO' | 'WARN' | 'ERROR' | 'DEBUG'

export type GamePhase =
  | 'role_assignment'
  | 'round_start'
  | 'interaction'
  | 'discussion'
  | 'voting'
  | 'result'
  | 'game_over'

export interface PlatformMetrics {
  players_online: number
  active_rooms: number
  games_running: number
  connected_websockets: number
  avg_game_duration_seconds: number
  avg_round_duration_seconds: number
  messages_per_second: number
  coordinator_win_rate: number
  mission_success_rate: number
  ai_accuracy: number
  replay_generation_time_ms: number
  backend_response_time_ms: number
  error_rate: number
}

export interface ServiceHealth {
  id: string
  name: string
  status: ServiceStatus
  latency_ms: number
  version: string
  uptime_seconds: number
  last_check: string
  deployment_target?: string
  details?: Record<string, string | number>
}

export interface RedisMetrics {
  memory_used_mb: number
  memory_peak_mb: number
  memory_max_mb: number
  connected_clients: number
  pubsub_channels: number
  total_keys: number
  expired_keys: number
  ops_per_sec: number
  hit_rate: number
  evicted_keys: number
}

export interface PostgresMetrics {
  active_connections: number
  max_connections: number
  query_latency_p50_ms: number
  query_latency_p95_ms: number
  database_size_mb: number
  table_count: number
  total_rows: number
  migration_version: string
  replication_lag_ms: number | null
  transactions_per_sec: number
  cache_hit_rate: number
}

export interface ActiveMatch {
  game_id: number
  room_code: string
  players: MatchPlayer[]
  current_round: number
  total_rounds: number
  current_phase: GamePhase
  elapsed_seconds: number
  coordinator_hidden: boolean
  avg_latency_ms: number
  signal_ai_usage: number
  replay_available: boolean
}

export interface MatchPlayer {
  user_id: number
  username: string
  role: string
  is_alive: boolean
}

export interface ActivityEvent {
  id: string
  type: string
  label: string
  icon: string
  timestamp: string
  details?: Record<string, string | number>
  level?: 'normal' | 'highlight' | 'warning'
}

export interface SignalAIMetrics {
  model_version: string
  avg_confidence: number
  avg_prediction_time_ms: number
  inference_queue: number
  predictions_today: number
  coordinator_accuracy: number
  false_positives: number
  false_negatives: number
  total_predictions: number
  training_samples: number
  feature_importance: FeatureImportance[]
}

export interface FeatureImportance {
  feature: string
  importance: number
}

export interface ReplayMetrics {
  games_recorded: number
  events_stored: number
  avg_generation_time_ms: number
  avg_replay_size_kb: number
  largest_replay_kb: number
  replay_queue: number
  total_replay_time_ms: number
  events_per_game_avg: number
}

export interface AnalyticsMetrics {
  games_per_day: GameDayCount[]
  player_retention: RetentionBucket[]
  conversation_volume: ConversationPoint[]
  avg_messages_per_game: number
  avg_round_duration: number
  most_common_missions: MissionStat[]
  coordinator_win_rate_trend: WinRatePoint[]
}

export interface GameDayCount {
  date: string
  count: number
}

export interface RetentionBucket {
  label: string
  percentage: number
}

export interface ConversationPoint {
  date: string
  messages: number
}

export interface MissionStat {
  type: string
  count: number
  completion_rate: number
}

export interface WinRatePoint {
  date: string
  rate: number
}

export interface LogEntry {
  id: string
  timestamp: string
  level: LogLevel
  source: string
  message: string
  metadata?: Record<string, string | number>
}

export interface ChartDataPoint {
  label: string
  value: number
  color?: string
}

export interface TimeSeriesPoint {
  timestamp: string
  value: number
}

export interface AdminNavSection {
  id: string
  label: string
  icon: string
  children?: AdminNavItem[]
}

export interface AdminNavItem {
  id: string
  label: string
  path: string
  icon: string
}
