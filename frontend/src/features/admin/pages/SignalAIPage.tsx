import { useState, useEffect } from 'react'
import { AdminTopBar } from '../components/TopBar'
import { MetricCard } from '../components/MetricCard'
import { MetricGrid } from '../components/MetricGrid'
import { ChartCard } from '../components/ChartCard'
import { Donut } from '../components/Donut'
import { fetchSignalAIMetrics } from '../services/adminApi'

import type { SignalAIMetrics } from '../types/admin.types'

export function SignalAIPage() {
  const [metrics, setMetrics] = useState<SignalAIMetrics | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchSignalAIMetrics().then((m) => {
      setMetrics(m)
      setLoading(false)
    })
  }, [])

  if (loading || !metrics) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-xs font-mono text-gray-600 animate-pulse">
          <span className="text-accent">{'//'}</span> Loading Signal AI...
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <AdminTopBar
        title="Signal AI"
        subtitle="ML model monitoring and performance"
      />

      {/* Primary Metrics */}
      <MetricGrid columns={4}>
        <MetricCard
          label="Model Version"
          value={metrics.model_version}
        />
        <MetricCard
          label="Avg Confidence"
          value={`${metrics.avg_confidence}%`}
        />
        <MetricCard
          label="Avg Prediction Time"
          value={`${metrics.avg_prediction_time_ms}ms`}
        />
        <MetricCard
          label="Predictions Today"
          value={metrics.predictions_today}
        />
      </MetricGrid>

      <MetricGrid columns={4}>
        <MetricCard
          label="Coordinator Accuracy"
          value={`${metrics.coordinator_accuracy}%`}
          change={0.5}
          changeLabel="vs baseline"
        />
        <MetricCard
          label="False Positives"
          value={metrics.false_positives}
        />
        <MetricCard
          label="False Negatives"
          value={metrics.false_negatives}
        />
        <MetricCard
          label="Inference Queue"
          value={metrics.inference_queue}
        />
      </MetricGrid>

      <div className="grid grid-cols-2 gap-3 max-lg:grid-cols-1">
        {/* Feature Importance */}
        <ChartCard title="Feature Importance" subtitle="Model feature weights">
          <div className="space-y-2">
            {metrics.feature_importance.map((fi) => (
              <div key={fi.feature} className="flex items-center gap-2">
                <span className="text-[10px] font-mono text-gray-500 w-36 truncate">
                  {fi.feature}
                </span>
                <div className="flex-1 h-2 bg-gray-800 rounded overflow-hidden">
                  <div
                    className="h-full bg-accent rounded transition-all duration-500"
                    style={{ width: `${fi.importance * 100}%` }}
                  />
                </div>
                <span className="text-[10px] font-mono text-gray-500 w-10 text-right">
                  {(fi.importance * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        </ChartCard>

        {/* Accuracy Overview */}
        <ChartCard title="Performance" subtitle="Classification metrics">
          <div className="flex items-center justify-center gap-8 py-4">
            <Donut
              value={metrics.coordinator_accuracy}
              max={100}
              size={80}
              color="#22c55e"
              label="Accuracy"
            />
            <div className="space-y-3">
              <div className="text-center">
                <div className="text-lg font-mono font-bold text-gray-200">
                  {metrics.total_predictions}
                </div>
                <div className="text-[10px] font-mono text-gray-600">Total Predictions</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-mono font-bold text-gray-200">
                  {metrics.training_samples}
                </div>
                <div className="text-[10px] font-mono text-gray-600">Training Samples</div>
              </div>
            </div>
          </div>
        </ChartCard>
      </div>
    </div>
  )
}
