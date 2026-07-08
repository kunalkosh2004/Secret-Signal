import { beginGoogleLogin } from '../services/authApi'

export function GoogleAuthButton() {
  const handleClick = () => {
    beginGoogleLogin()
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      className="
        w-full flex items-center justify-center gap-3
        px-4 py-2.5 border border-gray-400/30 rounded
        bg-gray-200 hover:bg-gray-250
        text-sm font-mono text-gray-700
        transition-colors
        focus:outline-none focus:ring-1 focus:ring-accent/50
      "
    >
      {/* Simple "G" icon — not a branded Google logo, just a visual indicator */}
      <span className="w-5 h-5 rounded-full bg-accent/10 border border-accent/30 flex items-center justify-center text-xs text-accent font-mono">
        G
      </span>
      Continue with Google
    </button>
  )
}
