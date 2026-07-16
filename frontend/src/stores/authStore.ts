import { create } from 'zustand'
import type { UserResponse } from '../features/auth/types/auth.types'

const TOKEN_KEY = 'secret_signal_token'
const USER_KEY = 'secret_signal_user'

interface AuthStore {
  user: UserResponse | null
  token: string | null
  isAuthenticated: boolean

  setAuth: (user: UserResponse, token: string) => void
  logout: () => void
  /** Load saved auth from localStorage (call on app mount) */
  loadFromStorage: () => void
}

function loadInitialAuth(): { user: UserResponse | null; token: string | null; isAuthenticated: boolean } {
  const token = localStorage.getItem(TOKEN_KEY)
  const raw = localStorage.getItem(USER_KEY)
  if (token && raw) {
    try {
      const user = JSON.parse(raw) as UserResponse
      return { user, token, isAuthenticated: true }
    } catch {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    }
  }
  return { user: null, token: null, isAuthenticated: false }
}

export const useAuthStore = create<AuthStore>((set) => ({
  ...loadInitialAuth(),

  setAuth: (user, token) => {
    localStorage.setItem(TOKEN_KEY, token)
    localStorage.setItem(USER_KEY, JSON.stringify(user))
    set({ user, token, isAuthenticated: true })
  },

  logout: () => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    set({ user: null, token: null, isAuthenticated: false })
  },

  loadFromStorage: () => {
    const token = localStorage.getItem(TOKEN_KEY)
    const raw = localStorage.getItem(USER_KEY)
    if (token && raw) {
      try {
        const user = JSON.parse(raw) as UserResponse
        set({ user, token, isAuthenticated: true })
      } catch {
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(USER_KEY)
      }
    }
  },
}))
