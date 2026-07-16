import { useAuthStore } from '../../../stores/authStore'

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

export async function startGame(roomCode: string) {
  return request<{ id: number }>(`/games/${roomCode}/start`, { method: 'POST' })
}

export async function advancePhase(gameId: number, nextPhase: string) {
  return request<{ id: number; phase: string; round_number: number; status: string }>(
    `/games/${gameId}/advance-phase`,
    {
      method: 'POST',
      body: JSON.stringify({ next_phase: nextPhase }),
    },
  )
}
