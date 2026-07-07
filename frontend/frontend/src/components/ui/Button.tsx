import { clsx } from 'clsx'
import { forwardRef } from 'react'

type Variant = 'default' | 'outline' | 'ghost'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  asChild?: boolean
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', asChild = false, children, ...props }, ref) => {
    const baseClasses = 'inline-flex items-center justify-center rounded-md text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-50 disabled:pointer-events-none disabled:opacity-50'
    const variantClasses = {
      default: 'bg-accent/90 text-gray-900 hover:bg-accent focus-visible:ring-accent glow-red',
      outline: 'border border-gray-500 text-gray-800 hover:bg-gray-200 hover:border-gray-400 focus-visible:ring-accent',
      ghost: 'text-gray-600 hover:text-gray-900 hover:bg-gray-200 focus-visible:ring-accent',
    }

    const Component = asChild ? 'span' : 'button'

    return (
      <Component
        className={clsx(
          baseClasses,
          variantClasses[variant],
          className
        )}
        ref={ref as React.Ref<HTMLButtonElement>}
        {...props}
      >
        {children}
      </Component>
    )
  }
)
Button.displayName = 'Button'