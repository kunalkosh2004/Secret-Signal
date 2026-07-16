interface SparkBarProps {
  data: { label: string; value: number }[]
  height?: number
  color?: string
  showLabels?: boolean
}

export function SparkBar({
  data,
  height = 60,
  color = '#ef4444',
  showLabels = false,
}: SparkBarProps) {
  const max = Math.max(...data.map((d) => d.value), 1)

  return (
    <div>
      <div className="flex items-end gap-px" style={{ height }}>
        {data.map((d, i) => {
          const h = Math.max(2, (d.value / max) * height)
          return (
            <div
              key={i}
              className="flex-1 group relative"
              style={{ height }}
              title={`${d.label}: ${d.value}`}
            >
              <div
                className="absolute bottom-0 w-full rounded-t-sm transition-all duration-300 group-hover:opacity-80"
                style={{ height: h, backgroundColor: color }}
              />
            </div>
          )
        })}
      </div>
      {showLabels && (
        <div className="flex gap-px mt-1">
          {data.map((d, i) => (
            <div
              key={i}
              className="flex-1 text-center text-[8px] font-mono text-gray-600 truncate"
            >
              {d.label}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
