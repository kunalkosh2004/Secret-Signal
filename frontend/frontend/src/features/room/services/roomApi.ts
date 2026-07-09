import type { CreateRoomRequest, JoinRoomRequest, RoomResponse } from '../types/room.types'
import type { ApiErrorResponse } from '../../auth/types/auth.types'
import { useAuthStore } from '../../../stores/authStore'

const BASE = '/api/v1/rooms'

function authHeaders(): Record<string, string> {
  const token = useAuthStore.getState().token
  if (!token) throw new Error('Not authenticated')
  return { Authorization: `Bearer ${token}` }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options.headers as Record<string, string> },
  })

  if (!res.ok) {
    let detail = 'An unexpected error occurred.'
    try {
      const err = (await res.json()) as ApiErrorResponse
      if (err.detail) detail = err.detail
    } catch {
      // ignore parse errors
    }
    throw new Error(detail)
  }

  return res.json() as Promise<T>
}

export async function createRoom(data: CreateRoomRequest): Promise<RoomResponse> {
  return request<RoomResponse>('', {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify(data),
  })
}

export async function joinRoom(data: JoinRoomRequest): Promise<RoomResponse> {
  return request<RoomResponse>('/join', {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify(data),
  })
}

export async function getRoom(code: string): Promise<RoomResponse> {
  return request<RoomResponse>(`/${code}`, {
    headers: authHeaders(),
  })
}

export async function leaveRoom(code: string): Promise<RoomResponse> {
  return request<RoomResponse>(`/${code}/leave`, {
    method: 'POST',
    headers: authHeaders(),
  })
}
