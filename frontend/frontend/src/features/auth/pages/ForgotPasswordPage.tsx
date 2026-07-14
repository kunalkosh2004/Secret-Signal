import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AuthLayout } from '../components/AuthLayout'
import { forgotPassword, resetPassword } from '../services/authApi'

type Step = 'email' | 'reset' | 'success'

export function ForgotPasswordPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState<Step>('email')
  const [email, setEmail] = useState('')
  const [resetToken, setResetToken] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const handleRequestReset = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)

    try {
      const result = await forgotPassword({ email: email.trim() })
      // In dev, we get the token back directly
      if (result.reset_token) {
        setResetToken(result.reset_token)
        setStep('reset')
      } else {
        // In production, token would be emailed
        setStep('success')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    setSubmitting(true)
    try {
      await resetPassword({ token: resetToken, new_password: newPassword })
      setStep('success')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="space-y-1">
          <h1 className="text-xl font-mono tracking-wider text-gray-900">
            <span className="text-accent">&gt;</span> {step === 'email' ? 'Reset Password' : step === 'reset' ? 'Set New Password' : 'Password Reset'}
          </h1>
          <p className="text-sm text-gray-600 font-mono">
            {step === 'email'
              ? 'Enter your email to receive a reset link.'
              : step === 'reset'
              ? 'Enter your new password below.'
              : 'Your password has been reset successfully.'}
          </p>
        </div>

        {/* Step: Email */}
        {step === 'email' && (
          <form onSubmit={handleRequestReset} className="space-y-5" noValidate>
            <div className="space-y-1.5">
              <label htmlFor="reset-email" className="block text-xs font-mono tracking-wider text-gray-700 uppercase">
                Email
              </label>
              <input
                id="reset-email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={submitting}
                placeholder="you@example.com"
                className="w-full bg-gray-200 border border-gray-400/30 rounded px-3 py-2.5 text-sm text-gray-900 font-mono placeholder:text-gray-600 focus:outline-none focus:ring-1 focus:ring-accent/50 focus:border-accent/50 transition-colors disabled:opacity-50"
              />
            </div>

            {error && (
              <div className="bg-red-500/10 border border-red-500/30 rounded px-3 py-2" role="alert">
                <p className="text-xs text-red-500 font-mono">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={submitting || !email.trim()}
              className="w-full px-4 py-2.5 border border-accent/50 rounded bg-accent/10 hover:bg-accent/20 text-sm font-mono tracking-wider text-gray-900 transition-all disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-1 focus:ring-accent/50"
            >
              {submitting ? 'SENDING...' : 'SEND RESET LINK'}
            </button>

            <button
              type="button"
              onClick={() => navigate('/auth')}
              className="w-full text-center text-xs font-mono text-gray-600 hover:text-gray-900 transition-colors"
            >
              Back to Login
            </button>
          </form>
        )}

        {/* Step: Reset Password */}
        {step === 'reset' && (
          <form onSubmit={handleResetPassword} className="space-y-5" noValidate>
            <div className="space-y-1.5">
              <label htmlFor="new-password" className="block text-xs font-mono tracking-wider text-gray-700 uppercase">
                New Password
              </label>
              <input
                id="new-password"
                type="password"
                autoComplete="new-password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                disabled={submitting}
                placeholder="At least 8 characters"
                className="w-full bg-gray-200 border border-gray-400/30 rounded px-3 py-2.5 text-sm text-gray-900 font-mono placeholder:text-gray-600 focus:outline-none focus:ring-1 focus:ring-accent/50 focus:border-accent/50 transition-colors disabled:opacity-50"
              />
            </div>

            <div className="space-y-1.5">
              <label htmlFor="confirm-password" className="block text-xs font-mono tracking-wider text-gray-700 uppercase">
                Confirm Password
              </label>
              <input
                id="confirm-password"
                type="password"
                autoComplete="new-password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                disabled={submitting}
                placeholder="Re-enter password"
                className="w-full bg-gray-200 border border-gray-400/30 rounded px-3 py-2.5 text-sm text-gray-900 font-mono placeholder:text-gray-600 focus:outline-none focus:ring-1 focus:ring-accent/50 focus:border-accent/50 transition-colors disabled:opacity-50"
              />
            </div>

            {error && (
              <div className="bg-red-500/10 border border-red-500/30 rounded px-3 py-2" role="alert">
                <p className="text-xs text-red-500 font-mono">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={submitting || !newPassword || !confirmPassword}
              className="w-full px-4 py-2.5 border border-accent/50 rounded bg-accent/10 hover:bg-accent/20 text-sm font-mono tracking-wider text-gray-900 transition-all disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-1 focus:ring-accent/50"
            >
              {submitting ? 'RESETTING...' : 'RESET PASSWORD'}
            </button>
          </form>
        )}

        {/* Step: Success */}
        {step === 'success' && (
          <div className="space-y-5 text-center">
            <div className="p-4 bg-green-500/10 border border-green-500/30 rounded">
              <p className="text-sm font-mono text-green-500">
                Password reset successfully! You can now log in with your new password.
              </p>
            </div>
            <button
              onClick={() => navigate('/auth')}
              className="w-full px-4 py-2.5 border border-accent/50 rounded bg-accent/10 hover:bg-accent/20 text-sm font-mono tracking-wider text-gray-900 transition-all"
            >
              GO TO LOGIN
            </button>
          </div>
        )}
      </div>
    </AuthLayout>
  )
}
