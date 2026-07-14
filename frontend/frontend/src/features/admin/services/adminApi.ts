/**
 * Admin API service layer.
 *
 * Currently returns mock data. When backend endpoints are implemented,
 * each function will make a real HTTP request. The mock providers are
 * centralized in mocks/dashboardData.ts so swapping requires changes
 * only in this file.
 *
 * Future endpoints:
 *   GET /admin/metrics
 *   GET /admin/games
 *   GET /admin/infrastructure
 *   GET /admin/replay
 *   GET /admin/analytics
 *   GET /admin/ai
 *   GET /admin/logs
 */

import {
  getPlatformMetrics,
  getServices,
  getRedisMetrics,
  getPostgresMetrics,
  getActiveMatches,
  getActivityFeed,
  getSignalAIMetrics,
  getReplayMetrics,
  getAnalyticsMetrics,
  getLogEntries,
  getHourlyMessageVolume,
  getHourlyPlayerCount,
  getBackendLatencyHistory,
} from '../mocks/dashboardData'

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

// Simulate network latency for realistic loading states
function withDelay<T>(data: T, ms = 150): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(data), ms))
}

export async function fetchPlatformMetrics(): Promise<PlatformMetrics> {
  // TODO: GET /admin/metrics
  return withDelay(getPlatformMetrics())
}

export async function fetchServices(): Promise<ServiceHealth[]> {
  // TODO: GET /admin/infrastructure
  return withDelay(getServices())
}

export async function fetchRedisMetrics(): Promise<RedisMetrics> {
  // TODO: GET /admin/infrastructure/redis
  return withDelay(getRedisMetrics())
}

export async function fetchPostgresMetrics(): Promise<PostgresMetrics> {
  // TODO: GET /admin/infrastructure/postgres
  return withDelay(getPostgresMetrics())
}

export async function fetchActiveMatches(): Promise<ActiveMatch[]> {
  // TODO: GET /admin/games
  return withDelay(getActiveMatches())
}

export async function fetchActivityFeed(): Promise<ActivityEvent[]> {
  // TODO: GET /admin/activity (future WebSocket)
  return withDelay(getActivityFeed())
}

export async function fetchSignalAIMetrics(): Promise<SignalAIMetrics> {
  // TODO: GET /admin/ai
  return withDelay(getSignalAIMetrics())
}

export async function fetchReplayMetrics(): Promise<ReplayMetrics> {
  // TODO: GET /admin/replay
  return withDelay(getReplayMetrics())
}

export async function fetchAnalyticsMetrics(): Promise<AnalyticsMetrics> {
  // TODO: GET /admin/analytics
  return withDelay(getAnalyticsMetrics())
}

export async function fetchLogEntries(): Promise<LogEntry[]> {
  // TODO: GET /admin/logs (future WebSocket tail)
  return withDelay(getLogEntries())
}

export async function fetchHourlyMessageVolume(): Promise<TimeSeriesPoint[]> {
  // TODO: GET /admin/analytics/messages
  return withDelay(getHourlyMessageVolume())
}

export async function fetchHourlyPlayerCount(): Promise<TimeSeriesPoint[]> {
  // TODO: GET /admin/analytics/players
  return withDelay(getHourlyPlayerCount())
}

export async function fetchBackendLatencyHistory(): Promise<TimeSeriesPoint[]> {
  // TODO: GET /admin/infrastructure/latency
  return withDelay(getBackendLatencyHistory())
}
