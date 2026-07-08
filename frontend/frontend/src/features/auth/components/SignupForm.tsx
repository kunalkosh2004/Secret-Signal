import { useState } from 'react'
import type { FormErrors } from '../types/auth.types'
import { validateSignupForm, PASSWORD_MIN_LENGTH } from '../validation/authValidation'
import { signup } from '../services/authApi'
import { PasswordField } from './PasswordField'
import { GoogleAuthButton } from './GoogleAuthButton'

interface SignupFormProps {
  onSuccess: () => void
}

export function SignupForm({ onSuccess }: SignupFormProps) {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [errors, setErrors] = useState<FormErrors>({})
  const [submitting, setSubmitting] = useState(false)
  const [serverError, setServerError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setServerError(null)

    const validationErrors = validateSignupForm({
      username,
      email,
      password,
      confirmPassword,
    })
    setErrors(validationErrors)
    if (Object.keys(validationErrors).length > 0) return

    setSubmitting(true)
    try {
      await signup({ username: username.trim(), email: email.trim(), password })
      onSuccess()
    } catch (err) {
      setServerError(
        err instanceof Error
          ? err.message
          : 'An unexpected error occurred.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      {/* Username */}
      <div className="space-y-1.5">
        <label htmlFor="signup-username" className="block text-xs font-mono tracking-wider text-gray-700 uppercase">
          Username
        </label>
        <input
          id="signup-username"
          type="text"
          autoComplete="username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          disabled={submitting}
          placeholder="Your in-game identity"
          className={`
            w-full bg-gray-200 border rounded px-3 py-2.5 text-sm text-gray-900
            font-mono placeholder:text-gray-600
            focus:outline-none focus:ring-1 focus:ring-accent/50 focus:border-accent/50
            transition-colors disabled:opacity-50
            ${errors.username ? 'border-red-500/60' : 'border-gray-400/30'}
          `}
        />
        {errors.username && (
          <p className="text-xs text-red-500 font-mono" role="alert">{errors.username}</p>
        )}
      </div>

      {/* Email */}
      <div className="space-y-1.5">
        <label htmlFor="signup-email" className="block text-xs font-mono tracking-wider text-gray-700 uppercase">
          Email
        </label>
        <input
          id="signup-email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          disabled={submitting}
          placeholder="you@example.com"
          className={`
            w-full bg-gray-200 border rounded px-3 py-2.5 text-sm text-gray-900
            font-mono placeholder:text-gray-600
            focus:outline-none focus:ring-1 focus:ring-accent/50 focus:border-accent/50
            transition-colors disabled:opacity-50
            ${errors.email ? 'border-red-500/60' : 'border-gray-400/30'}
          `}
        />
        {errors.email && (
          <p className="text-xs text-red-500 font-mono" role="alert">{errors.email}</p>
        )}
      </div>

      {/* Password */}
      <PasswordField
        label="Password"
        id="signup-password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        disabled={submitting}
        autoComplete="new-password"
        error={errors.password}
        hint={`At least ${PASSWORD_MIN_LENGTH} characters`}
      />

      {/* Confirm Password */}
      <PasswordField
        label="Confirm Password"
        id="signup-confirm"
        value={confirmPassword}
        onChange={(e) => setConfirmPassword(e.target.value)}
        disabled={submitting}
        autoComplete="new-password"
        error={errors.confirmPassword}
      />

      {/* Password requirements hint */}
      <div className="text-xs text-gray-600 font-mono space-y-0.5">
        <p>Password must:</p>
        <ul className="pl-4 list-disc space-y-0.5 text-gray-600">
          <li className={password.length >= PASSWORD_MIN_LENGTH ? 'text-green-500' : ''}>
            Be at least {PASSWORD_MIN_LENGTH} characters
          </li>
          <li className={/[A-Z]/.test(password) ? 'text-green-500' : ''}>
            Contain an uppercase letter
          </li>
          <li className={/[a-z]/.test(password) ? 'text-green-500' : ''}>
            Contain a lowercase letter
          </li>
          <li className={/[0-9]/.test(password) ? 'text-green-500' : ''}>
            Contain a number
          </li>
        </ul>
      </div>

      {/* Server error */}
      {serverError && (
        <div className="bg-red-500/10 border border-red-500/30 rounded px-3 py-2" role="alert">
          <p className="text-xs text-red-500 font-mono">{serverError}</p>
        </div>
      )}

      {/* Submit */}
      <button
        type="submit"
        disabled={submitting}
        className="
          w-full px-4 py-2.5 border border-accent/50 rounded
          bg-accent/10 hover:bg-accent/20
          text-sm font-mono tracking-wider text-gray-900
          transition-all disabled:opacity-50 disabled:cursor-not-allowed
          focus:outline-none focus:ring-1 focus:ring-accent/50
          glow-red
        "
      >
        {submitting ? 'CREATING ACCOUNT...' : 'CREATE ACCOUNT'}
      </button>

      {/* Divider */}
      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-gray-400/30" />
        </div>
        <div className="relative flex justify-center">
          <span className="bg-gray-100 px-3 text-xs text-gray-600 font-mono">OR</span>
        </div>
      </div>

      {/* Google */}
      <GoogleAuthButton />
    </form>
  )
}
