import type { AuthMode } from '../types/auth.types'

interface AuthModeSwitchProps {
  mode: AuthMode
  onToggle: () => void
}

export function AuthModeSwitch({ mode, onToggle }: AuthModeSwitchProps) {
  return (
    <p className="text-sm text-gray-600 font-mono text-center">
      {mode === 'login' ? (
        <>
          Don&apos;t have an account?{' '}
          <button
            type="button"
            onClick={onToggle}
            className="text-accent hover:text-accent/80 underline underline-offset-2 transition-colors"
          >
            Create account
          </button>
        </>
      ) : (
        <>
          Already have an account?{' '}
          <button
            type="button"
            onClick={onToggle}
            className="text-accent hover:text-accent/80 underline underline-offset-2 transition-colors"
          >
            Log in
          </button>
        </>
      )}
    </p>
  )
}
