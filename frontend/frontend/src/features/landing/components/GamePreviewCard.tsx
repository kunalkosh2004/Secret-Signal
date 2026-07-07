import { ProgressBar } from './ProgressBar'

interface GamePreviewCardProps {
  title: string
  description: string
  progress: number
  total: number
}

export const GamePreviewCard = ({
  title,
  description,
  progress,
  total,
}: GamePreviewCardProps) => {
  return (
    <div className="bg-gray-200 border border-gray-400/30 rounded p-5">
      <h3 className="text-sm font-mono tracking-wider text-accent mb-3">
        {'>'} {title}
      </h3>
      <p className="text-sm text-gray-600 mb-4">{description}</p>
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs font-mono text-gray-600">
          <span>PROGRESS</span>
          <span className="font-medium text-gray-700">{progress}/{total}</span>
        </div>
        <ProgressBar value={progress} total={total} />
      </div>
      {progress === total && (
        <div className="mt-4 text-xs font-mono text-green-500 border border-green-500/30 bg-green-500/10 rounded px-2 py-1 inline-block">
          MISSION COMPLETE
        </div>
      )}
    </div>
  )
}