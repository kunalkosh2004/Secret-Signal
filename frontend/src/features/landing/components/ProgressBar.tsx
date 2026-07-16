interface ProgressBarProps {
  value: number
  total: number
}

export const ProgressBar = ({ value, total }: ProgressBarProps) => {
  const percentage = (value / total) * 100
  return (
    <div className="w-full bg-gray-300 rounded-sm h-2">
      <div
        className="bg-accent/80 h-2 rounded-sm transition-all"
        style={{ width: `${percentage}%` }}
      ></div>
    </div>
  )
}