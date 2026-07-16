/**
 * Auth types — API contract types for authentication.
 *
 * These match the backend responses exactly:
 *   POST /api/v1/auth/signup → TokenResponse
 *   POST /api/v1/auth/login  → TokenResponse
 *   GET  /api/v1/auth/me     → UserResponse
 *
 * === Token storage ===
 * The access token is stored in localStorage and loaded on app start.
 * This is simple but XSS-vulnerable. In production, consider an
 * HttpOnly refresh cookie instead. See backend/app/auth/README.md.
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
  id: number
  username: string
  email: string
  created_at: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: UserResponse
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

export interface ForgotPasswordRequest {
  email: string
}

export interface ForgotPasswordResponse {
  message: string
  reset_token?: string
}

export interface ResetPasswordRequest {
  token: string
  new_password: string
}

export interface ResetPasswordResponse {
  message: string
}
