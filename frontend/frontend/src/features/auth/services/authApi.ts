/**
 * Auth API service boundary.
 *
 * Each function maps to a backend endpoint.
 * The backend does not exist yet, so these throw a development-time error
 * to make it obvious that the real implementation is missing.
 *
 * === Integration checklist (do this later) ===
 *
 * 1. Pick an HTTP client: plain `fetch`, ky, or axios.
 *    The rest of this project doesn't use one yet, so start with fetch.
 *
 * 2. Decide where the base URL comes from.
 *    The Vite dev server proxies /api/* to the backend,
 *    so in development you can use relative URLs like `/api/v1/auth/signup`.
 *
 * 3. Decide how to store the access token.
 *    See the auth README for trade-offs.
 *    Popular options: in-memory variable + HttpOnly refresh cookie,
 *    or localStorage (with XSS awareness).
 *
 * 4. Add an interceptor / wrapper that attaches the token
 *    to the Authorization header on every request.
 */

import type { SignupRequest, LoginRequest, AuthResponse } from '../types/auth.types'

const DEV_MESSAGE = 'Backend auth endpoints are not yet implemented.'

async function devNotImplemented(): Promise<never> {
  throw new Error(
    `${DEV_MESSAGE} See backend/app/auth/README.md to implement them yourself.`,
  )
}

export async function signup(_data: SignupRequest): Promise<AuthResponse> {
  // TODO: POST /api/v1/auth/signup
  return devNotImplemented()
}

export async function login(_data: LoginRequest): Promise<AuthResponse> {
  // TODO: POST /api/v1/auth/login
  return devNotImplemented()
}

export async function logout(): Promise<void> {
  // TODO: POST /api/v1/auth/logout
  return devNotImplemented()
}

export async function getCurrentUser(): Promise<AuthResponse['user']> {
  // TODO: GET /api/v1/auth/me
  return devNotImplemented()
}

/**
 * Begin Google OAuth login flow.
 *
 * Future implementation: redirect the browser to
 *   GET /api/v1/auth/google/login
 *
 * The backend will redirect to Google's consent screen,
 * then after auth, Google redirects back to the backend callback,
 * which creates/links the account and sets an application session.
 *
 * Do NOT:
 *   - Hardcode a Google client ID here
 *   - Call Google's APIs directly from the browser
 *   - Store OAuth secrets in the frontend bundle
 */
export function beginGoogleLogin(): void {
  // TODO: window.location.href = '/api/v1/auth/google/login'
  console.warn(
    'Google login is not yet configured. ' +
    'Implement the backend OAuth flow first (see backend/app/auth/README.md).',
  )
}
