import { useAuthStore } from '../../../stores/authStore'
import type { ReplayTimeline, ReplayStateSnapshot } from '../types/replay.types'

const API_BASE = '/api/v1'

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = useAuthStore.getState().token
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { ...headers, ...(options.headers as Record<string, string> ?? {}) },
  })

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? `HTTP ${res.status}`)
  }

  return res.json()
}

export async function getReplayTimeline(gameId: number): Promise<ReplayTimeline> {
  return request<ReplayTimeline>(`/replay/${gameId}`)
}

export async function getReplaySnapshot(
  gameId: number,
  sequenceNumber: number,
): Promise<ReplayStateSnapshot> {
  return request<ReplayStateSnapshot>(
    `/replay/${gameId}/snapshot?sequence_number=${sequenceNumber}`,
  )
}
