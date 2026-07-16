interface PlayerAvatarProps {
  name: string
  isCoordinator?: boolean
}

export const PlayerAvatar = ({ name, isCoordinator = false }: PlayerAvatarProps) => {
  const initials = name
    .split(' ')
    .map((part) => part[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)

  return (
    <div className="flex items-center space-x-3 px-3 py-2 rounded bg-gray-150 border border-gray-400/20 hover:border-gray-400/40 transition-colors">
      <div className="relative h-8 w-8 flex-shrink-0">
        <div className="h-8 w-8 rounded bg-gray-250 flex items-center justify-center border border-gray-400/30">
          <span className="text-xs font-mono text-gray-700">{initials}</span>
        </div>
        {isCoordinator && (
          <div className="absolute -inset-1 animate-pulse-glow rounded">
            <div className="absolute inset-0 rounded border border-accent/50"></div>
          </div>
        )}
      </div>
      <div className="flex items-center space-x-2">
        <span className="text-sm font-mono text-gray-700">{name}</span>
        {isCoordinator && (
          <span className="text-[10px] font-mono text-accent border border-accent/30 bg-accent/10 px-1.5 py-0.5 rounded">
            COORD
          </span>
        )}
      </div>
    </div>
  )
}