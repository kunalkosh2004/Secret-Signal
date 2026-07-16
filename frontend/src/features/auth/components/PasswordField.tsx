import { useState, type InputHTMLAttributes } from 'react'

interface PasswordFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  error?: string
  /** Optional hint text shown below the field (for signup password requirements) */
  hint?: string
}

export function PasswordField({
  label,
  error,
  hint,
  id,
  ...inputProps
}: PasswordFieldProps) {
  const [visible, setVisible] = useState(false)
  const inputId = id ?? label.toLowerCase().replace(/\s+/g, '-')

  return (
    <div className="space-y-1.5">
      <label htmlFor={inputId} className="block text-xs font-mono tracking-wider text-gray-700 uppercase">
        {label}
      </label>
      <div className="relative">
        <input
          id={inputId}
          type={visible ? 'text' : 'password'}
          autoComplete={inputProps.autoComplete ?? 'off'}
          className={`
            w-full bg-gray-200 border rounded px-3 py-2.5 text-sm text-gray-900
            font-mono placeholder:text-gray-600
            focus:outline-none focus:ring-1 focus:ring-accent/50 focus:border-accent/50
            transition-colors
            ${error ? 'border-red-500/60' : 'border-gray-400/30'}
          `}
          {...inputProps}
        />
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          className="absolute right-2.5 top-1/2 -translate-y-1/2 text-xs font-mono text-gray-600 hover:text-gray-800 transition-colors px-1.5 py-0.5 rounded bg-gray-300/50"
          aria-label={visible ? 'Hide password' : 'Show password'}
          tabIndex={-1}
        >
          {visible ? 'HIDE' : 'SHOW'}
        </button>
      </div>
      {error && (
        <p className="text-xs text-red-500 font-mono" role="alert">
          {error}
        </p>
      )}
      {hint && !error && (
        <p className="text-xs text-gray-600 font-mono">{hint}</p>
      )}
    </div>
  )
}
