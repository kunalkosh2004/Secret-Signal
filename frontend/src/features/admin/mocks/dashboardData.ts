import type {
  PlatformMetrics,
  ServiceHealth,
  RedisMetrics,
  PostgresMetrics,
  ActiveMatch,
  ActivityEvent,
  SignalAIMetrics,
  ReplayMetrics,
  AnalyticsMetrics,
  LogEntry,
  TimeSeriesPoint,
} from '../types/admin.types'

// ---------------------------------------------------------------------------
// Platform Overview Metrics
// ---------------------------------------------------------------------------

export function getPlatformMetrics(): PlatformMetrics {
  return {
    players_online: 47,
    active_rooms: 8,
    games_running: 3,
    connected_websockets: 52,
    avg_game_duration_seconds: 540,
    avg_round_duration_seconds: 180,
    messages_per_second: 12.4,
    coordinator_win_rate: 58.3,
    mission_success_rate: 72.1,
    ai_accuracy: 73.3,
    replay_generation_time_ms: 340,
    backend_response_time_ms: 45,
    error_rate: 0.12,
  }
}

// ---------------------------------------------------------------------------
// Service Health
// ---------------------------------------------------------------------------

export function getServices(): ServiceHealth[] {
  return [
    {
      id: 'backend',
      name: 'FastAPI Backend',
      status: 'healthy',
      latency_ms: 45,
      version: '0.4.0',
      uptime_seconds: 259200,
      last_check: new Date().toISOString(),
      deployment_target: 'docker-compose',
    },
    {
      id: 'frontend',
      name: 'React Frontend',
      status: 'healthy',
      latency_ms: 12,
      version: '0.4.0',
      uptime_seconds: 259200,
      last_check: new Date().toISOString(),
      deployment_target: 'nginx',
    },
    {
      id: 'redis',
      name: 'Redis 7',
      status: 'healthy',
      latency_ms: 2,
      version: '7.2.0',
      uptime_seconds: 259200,
      last_check: new Date().toISOString(),
      deployment_target: 'docker-compose',
    },
    {
      id: 'postgres',
      name: 'PostgreSQL 15',
      status: 'healthy',
      latency_ms: 8,
      version: '15.4',
      uptime_seconds: 259200,
      last_check: new Date().toISOString(),
      deployment_target: 'docker-compose',
    },
    {
      id: 'websocket',
      name: 'WebSocket Gateway',
      status: 'healthy',
      latency_ms: 3,
      version: '0.4.0',
      uptime_seconds: 259200,
      last_check: new Date().toISOString(),
      deployment_target: 'docker-compose',
    },
    {
      id: 'replay',
      name: 'Replay Engine',
      status: 'healthy',
      latency_ms: 120,
      version: '0.1.0',
      uptime_seconds: 259200,
      last_check: new Date().toISOString(),
      deployment_target: 'docker-compose',
    },
    {
      id: 'signal_ai',
      name: 'Signal AI',
      status: 'degraded',
      latency_ms: 230,
      version: '0.2.0',
      uptime_seconds: 86400,
      last_check: new Date().toISOString(),
      deployment_target: 'docker-compose',
      details: { note: 'Model retrain pending' },
    },
    {
      id: 'ml_worker',
      name: 'ML Worker',
      status: 'healthy',
      latency_ms: 85,
      version: '0.1.0',
      uptime_seconds: 259200,
      last_check: new Date().toISOString(),
      deployment_target: 'docker-compose',
    },
  ]
}

// ---------------------------------------------------------------------------
// Redis Metrics
// ---------------------------------------------------------------------------

export function getRedisMetrics(): RedisMetrics {
  return {
    memory_used_mb: 24.6,
    memory_peak_mb: 31.2,
    memory_max_mb: 256,
    connected_clients: 14,
    pubsub_channels: 8,
    total_keys: 1247,
    expired_keys: 892,
    ops_per_sec: 340,
    hit_rate: 94.7,
    evicted_keys: 0,
  }
}

// ---------------------------------------------------------------------------
// PostgreSQL Metrics
// ---------------------------------------------------------------------------

export function getPostgresMetrics(): PostgresMetrics {
  return {
    active_connections: 12,
    max_connections: 100,
    query_latency_p50_ms: 3.2,
    query_latency_p95_ms: 18.7,
    database_size_mb: 48.3,
    table_count: 14,
    total_rows: 12847,
    migration_version: 'f6a7b8c9d0e1',
    replication_lag_ms: null,
    transactions_per_sec: 85,
    cache_hit_rate: 99.2,
  }
}

// ---------------------------------------------------------------------------
// Active Matches
// ---------------------------------------------------------------------------

export function getActiveMatches(): ActiveMatch[] {
  return [
    {
      game_id: 46,
      room_code: 'WUEZ7S',
      players: [
        { user_id: 9, username: 'Alice', role: 'investigator', is_alive: true },
        { user_id: 10, username: 'Bob', role: 'investigator', is_alive: true },
        { user_id: 11, username: 'Charlie', role: 'investigator', is_alive: true },
        { user_id: 12, username: 'Dave', role: 'investigator', is_alive: true },
        { user_id: 13, username: 'Eve', role: 'coordinator', is_alive: true },
      ],
      current_round: 2,
      total_rounds: 3,
      current_phase: 'interaction',
      elapsed_seconds: 312,
      coordinator_hidden: true,
      avg_latency_ms: 32,
      signal_ai_usage: 1,
      replay_available: false,
    },
    {
      game_id: 47,
      room_code: 'KJ8M2N',
      players: [
        { user_id: 14, username: 'Frank', role: 'coordinator', is_alive: true },
        { user_id: 15, username: 'Grace', role: 'investigator', is_alive: true },
        { user_id: 16, username: 'Henry', role: 'investigator', is_alive: true },
      ],
      current_round: 1,
      total_rounds: 1,
      current_phase: 'discussion',
      elapsed_seconds: 156,
      coordinator_hidden: true,
      avg_latency_ms: 28,
      signal_ai_usage: 0,
      replay_available: false,
    },
    {
      game_id: 48,
      room_code: 'P3QR9T',
      players: [
        { user_id: 27, username: 'gft_alice', role: 'investigator', is_alive: true },
        { user_id: 28, username: 'gft_bob', role: 'coordinator', is_alive: true },
        { user_id: 29, username: 'gft_charlie', role: 'investigator', is_alive: false },
        { user_id: 30, username: 'gft_dave', role: 'investigator', is_alive: true },
      ],
      current_round: 3,
      total_rounds: 5,
      current_phase: 'voting',
      elapsed_seconds: 624,
      coordinator_hidden: true,
      avg_latency_ms: 41,
      signal_ai_usage: 2,
      replay_available: false,
    },
  ]
}

// ---------------------------------------------------------------------------
// Activity Feed
// ---------------------------------------------------------------------------

export function getActivityFeed(): ActivityEvent[] {
  const now = Date.now()
  const sec = (s: number) => new Date(now - s * 1000).toISOString()

  return [
    { id: 'a1', type: 'room_created', label: 'Room Created', icon: '\u{1F4E6}', timestamp: sec(3), details: { room: 'X7Y2K9' }, level: 'normal' },
    { id: 'a2', type: 'player_joined', label: 'Player Joined', icon: '\u{1F464}', timestamp: sec(8), details: { player: 'Alice', room: 'WUEZ7S' }, level: 'normal' },
    { id: 'a3', type: 'game_started', label: 'Game Started', icon: '\u25B6\uFE0F', timestamp: sec(15), details: { game_id: 48, players: 4 }, level: 'highlight' },
    { id: 'a4', type: 'round_started', label: 'Round Started', icon: '\u21BB', timestamp: sec(30), details: { game_id: 46, round: 2 }, level: 'normal' },
    { id: 'a5', type: 'mission_completed', label: 'Mission Completed', icon: '\u{1F3AF}', timestamp: sec(45), details: { game_id: 46, mission: 'message_length' }, level: 'highlight' },
    { id: 'a6', type: 'signal_ai_scan', label: 'Signal AI Scan', icon: '\u{1F916}', timestamp: sec(60), details: { game_id: 46, confidence: '78%' }, level: 'normal' },
    { id: 'a7', type: 'vote_cast', label: 'Vote Cast', icon: '\u{1F5F3}\uFE0F', timestamp: sec(75), details: { game_id: 48, round: 3 }, level: 'normal' },
    { id: 'a8', type: 'player_left', label: 'Player Left', icon: '\u{1F6AA}', timestamp: sec(90), details: { player: 'Charlie', room: 'WUEZ7S' }, level: 'warning' },
    { id: 'a9', type: 'replay_generated', label: 'Replay Generated', icon: '\u23EA', timestamp: sec(120), details: { game_id: 45, events: 63 }, level: 'normal' },
    { id: 'a10', type: 'ai_prediction', label: 'AI Prediction Finished', icon: '\u{1F9E0}', timestamp: sec(150), details: { game_id: 45, prediction: 'coordinator_wins' }, level: 'normal' },
    { id: 'a11', type: 'game_ended', label: 'Game Ended', icon: '\u25A0\uFE0F', timestamp: sec(180), details: { game_id: 45, winner: 'coordinator' }, level: 'highlight' },
    { id: 'a12', type: 'round_started', label: 'Round Started', icon: '\u21BB', timestamp: sec(210), details: { game_id: 47, round: 1 }, level: 'normal' },
  ]
}

// ---------------------------------------------------------------------------
// Signal AI Metrics
// ---------------------------------------------------------------------------

export function getSignalAIMetrics(): SignalAIMetrics {
  return {
    model_version: 'v0.2.1',
    avg_confidence: 73.3,
    avg_prediction_time_ms: 230,
    inference_queue: 0,
    predictions_today: 14,
    coordinator_accuracy: 73.3,
    false_positives: 2,
    false_negatives: 1,
    total_predictions: 47,
    training_samples: 75,
    feature_importance: [
      { feature: 'message_length_avg', importance: 0.23 },
      { feature: 'questions_asked_ratio', importance: 0.19 },
      { feature: 'topic_initiations', importance: 0.15 },
      { feature: 'voting_accuracy', importance: 0.12 },
      { feature: 'question_response_rate', importance: 0.10 },
      { feature: 'reply_rate', importance: 0.08 },
      { feature: 'reaction_diversity', importance: 0.07 },
      { feature: 'message_timing_variance', importance: 0.06 },
    ],
  }
}

// ---------------------------------------------------------------------------
// Replay Metrics
// ---------------------------------------------------------------------------

export function getReplayMetrics(): ReplayMetrics {
  return {
    games_recorded: 47,
    events_stored: 2340,
    avg_generation_time_ms: 340,
    avg_replay_size_kb: 12.4,
    largest_replay_kb: 48.7,
    replay_queue: 0,
    total_replay_time_ms: 15980,
    events_per_game_avg: 49.8,
  }
}

// ---------------------------------------------------------------------------
// Analytics Metrics
// ---------------------------------------------------------------------------

export function getAnalyticsMetrics(): AnalyticsMetrics {
  return {
    games_per_day: [
      { date: '2026-07-08', count: 5 },
      { date: '2026-07-09', count: 8 },
      { date: '2026-07-10', count: 12 },
      { date: '2026-07-11', count: 7 },
      { date: '2026-07-12', count: 15 },
      { date: '2026-07-13', count: 10 },
      { date: '2026-07-14', count: 3 },
    ],
    player_retention: [
      { label: '1 game', percentage: 100 },
      { label: '2 games', percentage: 72 },
      { label: '3 games', percentage: 54 },
      { label: '5 games', percentage: 38 },
      { label: '10+ games', percentage: 18 },
    ],
    conversation_volume: [
      { date: '07-08', messages: 45 },
      { date: '07-09', messages: 78 },
      { date: '07-10', messages: 112 },
      { date: '07-11', messages: 67 },
      { date: '07-12', messages: 143 },
      { date: '07-13', messages: 98 },
      { date: '07-14', messages: 34 },
    ],
    avg_messages_per_game: 24.6,
    avg_round_duration: 180,
    most_common_missions: [
      { type: 'message_length', count: 18, completion_rate: 0.72 },
      { type: 'question_answering', count: 15, completion_rate: 0.68 },
      { type: 'topic_initiation', count: 12, completion_rate: 0.83 },
      { type: 'agreement_count', count: 9, completion_rate: 0.56 },
      { type: 'reply_chain', count: 7, completion_rate: 0.71 },
    ],
    coordinator_win_rate_trend: [
      { date: '07-08', rate: 55 },
      { date: '07-09', rate: 62 },
      { date: '07-10', rate: 58 },
      { date: '07-11', rate: 50 },
      { date: '07-12', rate: 67 },
      { date: '07-13', rate: 54 },
      { date: '07-14', rate: 58 },
    ],
  }
}

// ---------------------------------------------------------------------------
// Log Entries
// ---------------------------------------------------------------------------

export function getLogEntries(): LogEntry[] {
  const now = Date.now()
  const sec = (s: number) => new Date(now - s * 1000).toISOString()

  return [
    { id: 'l1', timestamp: sec(2), level: 'INFO', source: 'game_engine', message: 'Game #48 advanced to phase voting' },
    { id: 'l2', timestamp: sec(5), level: 'INFO', source: 'ws_manager', message: 'WebSocket connected: user_id=27 room=WUEZ7S' },
    { id: 'l3', timestamp: sec(8), level: 'INFO', source: 'analytics', message: 'Analysis generated for game #45' },
    { id: 'l4', timestamp: sec(12), level: 'WARN', source: 'redis', message: 'Redis latency spike detected: 8ms avg (threshold: 5ms)' },
    { id: 'l5', timestamp: sec(15), level: 'INFO', source: 'replay_engine', message: 'Replay generated for game #45: 63 events, 12.4KB' },
    { id: 'l6', timestamp: sec(20), level: 'INFO', source: 'signal_ai', message: 'Signal AI scan completed for game #46: confidence 78%' },
    { id: 'l7', timestamp: sec(25), level: 'ERROR', source: 'replay_engine', message: 'Replay generation failed for game #44: timeout after 5000ms' },
    { id: 'l8', timestamp: sec(30), level: 'INFO', source: 'game_engine', message: 'Mission completed: message_length for game #46' },
    { id: 'l9', timestamp: sec(35), level: 'INFO', source: 'ws_manager', message: 'WebSocket disconnected: user_id=14 reason=client_close' },
    { id: 'l10', timestamp: sec(40), level: 'INFO', source: 'room', message: 'Room X7Y2K9 created by user_id=29' },
    { id: 'l11', timestamp: sec(45), level: 'WARN', source: 'analytics', message: 'Slow query detected: 45ms on game_events table' },
    { id: 'l12', timestamp: sec(50), level: 'INFO', source: 'training', message: 'ML model retrained: 75 samples, 73.3% accuracy, 17 features' },
    { id: 'l13', timestamp: sec(55), level: 'INFO', source: 'game_engine', message: 'Vote cast: user_id=28 target=29 in game #48' },
    { id: 'l14', timestamp: sec(60), level: 'INFO', source: 'auth', message: 'Password reset token consumed: user_id=6' },
    { id: 'l15', timestamp: sec(65), level: 'INFO', source: 'ws_manager', message: 'Room state broadcast: room=WUEZ7S players=5' },
  ]
}

// ---------------------------------------------------------------------------
// Time Series Generators (for charts)
// ---------------------------------------------------------------------------

export function getHourlyMessageVolume(): TimeSeriesPoint[] {
  const points: TimeSeriesPoint[] = []
  const now = Date.now()
  for (let i = 23; i >= 0; i--) {
    points.push({
      timestamp: new Date(now - i * 3600000).toISOString(),
      value: Math.floor(Math.random() * 40 + 5),
    })
  }
  return points
}

export function getHourlyPlayerCount(): TimeSeriesPoint[] {
  const points: TimeSeriesPoint[] = []
  const now = Date.now()
  for (let i = 23; i >= 0; i--) {
    points.push({
      timestamp: new Date(now - i * 3600000).toISOString(),
      value: Math.floor(Math.random() * 30 + 2),
    })
  }
  return points
}

export function getBackendLatencyHistory(): TimeSeriesPoint[] {
  const points: TimeSeriesPoint[] = []
  const now = Date.now()
  for (let i = 23; i >= 0; i--) {
    points.push({
      timestamp: new Date(now - i * 3600000).toISOString(),
      value: Math.floor(Math.random() * 30 + 25),
    })
  }
  return points
}
