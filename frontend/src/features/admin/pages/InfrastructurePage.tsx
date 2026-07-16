import { useState, useEffect } from 'react'
import { AdminTopBar } from '../components/TopBar'
import { MetricCard } from '../components/MetricCard'
import { MetricGrid } from '../components/MetricGrid'
import { Donut } from '../components/Donut'
import { ServiceStatusCard } from '../components/ServiceStatusCard'
import { SectionHeader } from '../components/SectionHeader'
import {
  fetchServices,
  fetchRedisMetrics,
  fetchPostgresMetrics,
} from '../services/adminApi'

import type {
  ServiceHealth,
  RedisMetrics,
  PostgresMetrics,
} from '../types/admin.types'

export function InfrastructurePage() {
  const [services, setServices] = useState<ServiceHealth[]>([])
  const [redis, setRedis] = useState<RedisMetrics | null>(null)
  const [postgres, setPostgres] = useState<PostgresMetrics | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([fetchServices(), fetchRedisMetrics(), fetchPostgresMetrics()]).then(
      ([s, r, p]) => {
        setServices(s)
        setRedis(r)
        setPostgres(p)
        setLoading(false)
      },
    )
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-xs font-mono text-gray-600 animate-pulse">
          <span className="text-accent">{'//'}</span> Loading infrastructure...
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <AdminTopBar
        title="Infrastructure"
        subtitle="Service health, Redis, and PostgreSQL monitoring"
      />

      {/* Service Grid */}
      <SectionHeader title="Services" subtitle="Health and performance" />
      <div className="grid grid-cols-4 gap-3 max-lg:grid-cols-2 max-sm:grid-cols-1">
        {services.map((service) => (
          <ServiceStatusCard key={service.id} {...service} />
        ))}
      </div>

      {/* Redis + PostgreSQL */}
      <div className="grid grid-cols-2 gap-3 max-lg:grid-cols-1">
        {/* Redis */}
        {redis && (
          <div>
            <SectionHeader title="Redis" subtitle="In-memory data store" />
            <div className="border border-gray-800/50 rounded bg-gray-950 p-4">
              <div className="flex items-start gap-6 mb-4">
                <div className="flex items-center gap-3">
                  <Donut
                    value={redis.memory_used_mb}
                    max={redis.memory_max_mb}
                    size={70}
                    color="#ef4444"
                    label="Memory"
                  />
                  <div className="text-[10px] font-mono text-gray-500">
                    {redis.memory_used_mb}MB / {redis.memory_max_mb}MB
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Donut
                    value={redis.hit_rate}
                    max={100}
                    size={70}
                    color="#22c55e"
                    label="Hit Rate"
                  />
                  <div className="text-[10px] font-mono text-gray-500">
                    {redis.hit_rate}%
                  </div>
                </div>
              </div>
              <MetricGrid columns={3}>
                <MetricCard label="Connected Clients" value={redis.connected_clients} compact />
                <MetricCard label="Total Keys" value={redis.total_keys} compact />
                <MetricCard label="Pub/Sub Channels" value={redis.pubsub_channels} compact />
                <MetricCard label="Ops/sec" value={redis.ops_per_sec} compact />
                <MetricCard label="Expired Keys" value={redis.expired_keys} compact />
                <MetricCard label="Evicted Keys" value={redis.evicted_keys} compact />
              </MetricGrid>
            </div>
          </div>
        )}

        {/* PostgreSQL */}
        {postgres && (
          <div>
            <SectionHeader title="PostgreSQL" subtitle="Relational database" />
            <div className="border border-gray-800/50 rounded bg-gray-950 p-4">
              <div className="flex items-start gap-6 mb-4">
                <div className="flex items-center gap-3">
                  <Donut
                    value={postgres.active_connections}
                    max={postgres.max_connections}
                    size={70}
                    color="#a78bfa"
                    label="Connections"
                  />
                  <div className="text-[10px] font-mono text-gray-500">
                    {postgres.active_connections} / {postgres.max_connections}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Donut
                    value={postgres.cache_hit_rate}
                    max={100}
                    size={70}
                    color="#22c55e"
                    label="Cache Hit"
                  />
                  <div className="text-[10px] font-mono text-gray-500">
                    {postgres.cache_hit_rate}%
                  </div>
                </div>
              </div>
              <MetricGrid columns={3}>
                <MetricCard label="Query P50" value={`${postgres.query_latency_p50_ms}ms`} compact />
                <MetricCard label="Query P95" value={`${postgres.query_latency_p95_ms}ms`} compact />
                <MetricCard label="DB Size" value={`${postgres.database_size_mb}MB`} compact />
                <MetricCard label="Tables" value={postgres.table_count} compact />
                <MetricCard label="Total Rows" value={postgres.total_rows} compact />
                <MetricCard
                  label="Replication Lag"
                  value={postgres.replication_lag_ms !== null ? `${postgres.replication_lag_ms}ms` : 'N/A'}
                  compact
                />
              </MetricGrid>
              <div className="mt-3 text-[10px] font-mono text-gray-600">
                Migration: <span className="text-gray-400">{postgres.migration_version}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
