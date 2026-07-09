/**
 * Auth API service — talks to the real backend.
 *
 * The Vite dev server proxies /api/* → http://localhost:8000,
 * so we use relative URLs in development.
 */

import type {
  SignupRequest,
  LoginRequest,
  AuthResponse,
  UserResponse,
  ApiErrorResponse,
} from '../types/auth.types'

const BASE = '/api/v1/auth'

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
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

/** Authenticated request helper — attaches Bearer token. */
function authHeaders(token: string): Record<string, string> {
  return { Authorization: `Bearer ${token}` }
}

// ── Public endpoints ──────────────────────────────────────────────

export async function signup(data: SignupRequest): Promise<AuthResponse> {
  return request<AuthResponse>('/signup', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function login(data: LoginRequest): Promise<AuthResponse> {
  return request<AuthResponse>('/login', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

// ── Authenticated endpoints ───────────────────────────────────────

export async function logout(): Promise<void> {
  // Stateless JWT — no server action needed, just clear on client.
  // The backend /logout endpoint exists but is a no-op.
}

export async function getCurrentUser(token: string): Promise<UserResponse> {
  return request<UserResponse>('/me', {
    headers: authHeaders(token),
  })
}

// ── Google OAuth ──────────────────────────────────────────────────

/**
 * Begin Google OAuth login flow.
 *
 * Redirects the browser to the backend, which redirects to Google.
 * After Google auth, the backend redirects back to the frontend
 * with a one-time handoff code (to be implemented).
 *
 * For now, this directly triggers the browser redirect.
 */
export function beginGoogleLogin(): void {
  window.location.href = `${BASE}/google/login`
}
