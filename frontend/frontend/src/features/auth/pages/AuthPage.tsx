import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import type { AuthMode } from '../types/auth.types'
import { AuthLayout } from '../components/AuthLayout'
import { LoginForm } from '../components/LoginForm'
import { SignupForm } from '../components/SignupForm'
import { AuthModeSwitch } from '../components/AuthModeSwitch'

export function AuthPage() {
  const navigate = useNavigate()
  const [mode, setMode] = useState<AuthMode>('login')

  const handleSuccess = () => {
    // TODO: After real auth is implemented, navigate to /lobby
    // For now, the API throws "not implemented" so this won't fire.
    navigate('/lobby')
  }

  return (
    <AuthLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="space-y-1">
          <h1 className="text-xl font-mono tracking-wider text-gray-900">
            {mode === 'login' ? (
              <><span className="text-accent">&gt;</span> Welcome Back</>
            ) : (
              <><span className="text-accent">&gt;</span> Join the Signal</>
            )}
          </h1>
          <p className="text-sm text-gray-600 font-mono">
            {mode === 'login'
              ? 'Return to the room. The signal is waiting.'
              : 'Create your identity before entering the game.'}
          </p>
        </div>

        {/* Form */}
        {mode === 'login' ? (
          <LoginForm onSuccess={handleSuccess} />
        ) : (
          <SignupForm onSuccess={handleSuccess} />
        )}

        {/* Mode switch */}
        <AuthModeSwitch
          mode={mode}
          onToggle={() => setMode((m) => (m === 'login' ? 'signup' : 'login'))}
        />
      </div>
    </AuthLayout>
  )
}
