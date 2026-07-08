/**
 * Auth types — API contract types for authentication.
 *
 * These define the shape of data sent to and received from the backend.
 * The backend is not fully implemented yet; these are the planned contracts.
 *
 * === Design Notes ===
 *
 * Token strategy: The current plan uses an access token returned in the JSON body.
 * A future iteration may switch to HttpOnly cookies for the refresh token.
 * See backend/app/auth/README.md for trade-offs.
 *
 * Nothing here is persisted in the frontend except ephemeral form state
 * and whatever token storage mechanism is finalised later.
 */

export interface SignupRequest {
  username: string
  email: string
  password: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface UserResponse {
  id: string
  username: string
  email: string
  createdAt: string
}

export interface AuthResponse {
  user: UserResponse
  /** JWT access token (or session token, depending on final architecture) */
  accessToken: string
}

export interface ApiErrorResponse {
  detail: string
}

export type AuthMode = 'login' | 'signup'

export interface FormErrors {
  username?: string
  email?: string
  password?: string
  confirmPassword?: string
  general?: string
}
