import { useAuthStore } from '../../../stores/authStore'
import type { GameAnalysis } from '../types/analysis.types'

import { API_V1 } from "../../../config/api";

const API_BASE = API_V1;

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

export async function getGameAnalysis(gameId: number): Promise<GameAnalysis> {
  return request<GameAnalysis>(`/analytics/${gameId}`)
}
