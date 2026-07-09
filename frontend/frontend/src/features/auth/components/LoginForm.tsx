import { useState } from 'react'
import type { FormErrors, AuthResponse } from '../types/auth.types'
import { validateLoginForm } from '../validation/authValidation'
import { login } from '../services/authApi'
import { PasswordField } from './PasswordField'
import { GoogleAuthButton } from './GoogleAuthButton'

interface LoginFormProps {
  onSuccess: (response: AuthResponse) => void
}

export function LoginForm({ onSuccess }: LoginFormProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState<FormErrors>({})
  const [submitting, setSubmitting] = useState(false)
  const [serverError, setServerError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setServerError(null)

    const validationErrors = validateLoginForm({ email, password })
    setErrors(validationErrors)
    if (Object.keys(validationErrors).length > 0) return

    setSubmitting(true)
    try {
      const result = await login({ email: email.trim(), password })
      onSuccess(result)
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
    <form onSubmit={handleSubmit} className="space-y-5" noValidate>
      {/* Email */}
      <div className="space-y-1.5">
        <label htmlFor="login-email" className="block text-xs font-mono tracking-wider text-gray-700 uppercase">
          Email
        </label>
        <input
          id="login-email"
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
        id="login-password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        disabled={submitting}
        autoComplete="current-password"
        error={errors.password}
      />

      {/* Forgot password — placeholder only */}
      <div className="flex justify-end">
        <span className="text-xs text-gray-600 font-mono cursor-not-allowed opacity-60">
          Forgot password? <span className="italic">(coming soon)</span>
        </span>
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
        {submitting ? 'AUTHENTICATING...' : 'LOG IN'}
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
