import type { FormErrors } from '../types/auth.types'

/**
 * Centralised validation rules for auth forms.
 *
 * These are user-facing conveniences only.
 * The backend validates everything again for security.
 *
 * Why validate twice?
 *   Frontend validation gives instant feedback (no round-trip).
 *   Backend validation is the source of truth — never trust the client.
 */

export const PASSWORD_MIN_LENGTH = 8

export function validateUsername(username: string): string | undefined {
  const trimmed = username.trim()
  if (!trimmed) return 'Username is required'
  if (trimmed.length < 2) return 'Username must be at least 2 characters'
  if (trimmed.length > 30) return 'Username must be 30 characters or fewer'
  return undefined
}

export function validateEmail(email: string): string | undefined {
  const trimmed = email.trim()
  if (!trimmed) return 'Email is required'
  // Basic structural check — backend does real validation
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed)) return 'Enter a valid email address'
  return undefined
}

export function validatePassword(password: string): string | undefined {
  if (!password) return 'Password is required'
  if (password.length < PASSWORD_MIN_LENGTH) {
    return `Password must be at least ${PASSWORD_MIN_LENGTH} characters`
  }
  return undefined
}

export function validateConfirmPassword(
  password: string,
  confirmPassword: string,
): string | undefined {
  if (!confirmPassword) return 'Please confirm your password'
  if (password !== confirmPassword) return 'Passwords do not match'
  return undefined
}

export function validateSignupForm(values: {
  username: string
  email: string
  password: string
  confirmPassword: string
}): FormErrors {
  const errors: FormErrors = {}
  const usernameErr = validateUsername(values.username)
  const emailErr = validateEmail(values.email)
  const passwordErr = validatePassword(values.password)
  const confirmErr = validateConfirmPassword(values.password, values.confirmPassword)

  if (usernameErr) errors.username = usernameErr
  if (emailErr) errors.email = emailErr
  if (passwordErr) errors.password = passwordErr
  if (confirmErr) errors.confirmPassword = confirmErr

  return errors
}

export function validateLoginForm(values: {
  email: string
  password: string
}): FormErrors {
  const errors: FormErrors = {}
  const emailErr = validateEmail(values.email)
  const passwordErr = validatePassword(values.password)

  if (emailErr) errors.email = emailErr
  if (passwordErr) errors.password = passwordErr

  return errors
}

/**
 * Returns true if the errors object has any field-level errors.
 */
export function hasErrors(errors: FormErrors): boolean {
  return Object.keys(errors).length > 0 && !errors.general
}
