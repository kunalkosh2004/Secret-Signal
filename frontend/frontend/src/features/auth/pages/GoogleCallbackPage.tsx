import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuthStore } from '../../../stores/authStore'
import { getCurrentUser } from '../services/authApi'

export function GoogleCallbackPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const setAuth = useAuthStore((s) => s.setAuth)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const token = searchParams.get('access_token')

    if (!token) {
      setError('No access token received from Google authentication.')
      return
    }

    getCurrentUser(token)
      .then((user) => {
        setAuth(user, token)
        navigate('/lobby', { replace: true })
      })
      .catch(() => {
        setError('Failed to verify your session. Please try logging in again.')
      })
  }, [searchParams, setAuth, navigate])

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 bg-grid flex items-center justify-center">
        <div className="text-center max-w-md px-4">
          <div className="text-sm font-mono tracking-wider text-gray-600 mb-2">
            <span className="text-accent">{'//'}</span> AUTH ERROR
          </div>
          <p className="text-gray-800 font-mono text-sm">{error}</p>
          <button
            onClick={() => navigate('/auth', { replace: true })}
            className="mt-6 px-4 py-2 border border-accent/50 text-sm font-mono rounded-md text-gray-900 bg-accent/10 hover:bg-accent/20 transition-all"
          >
            BACK TO LOGIN
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 bg-grid flex items-center justify-center">
      <div className="text-center">
        <div className="text-sm font-mono tracking-wider text-gray-600">
          <span className="text-accent">{'//'}</span> SIGNING IN...
        </div>
      </div>
    </div>
  )
}
