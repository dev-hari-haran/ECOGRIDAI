import React from 'react'
import clsx from 'clsx'

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'accent' | 'outline' | 'ghost' | 'danger'
  size?: 'xs' | 'sm' | 'md' | 'lg'
}

export function Button({
  variant = 'primary',
  size = 'md',
  className,
  children,
  type = 'button',
  ...props
}: ButtonProps) {
  const variantStyles: Record<NonNullable<ButtonProps['variant']>, string> = {
    primary:
      'bg-forest text-cornsilk hover:bg-forest-mid border border-forest shadow-xs disabled:opacity-50',
    secondary:
      'bg-olive text-cornsilk hover:bg-olive-light border border-olive shadow-xs disabled:opacity-50',
    accent:
      'bg-copper text-cornsilk hover:bg-copper-dark border border-copper shadow-xs disabled:opacity-50',
    outline:
      'bg-cornsilk-card text-forest hover:bg-cornsilk-soft border border-olive/35 disabled:opacity-50',
    ghost:
      'bg-transparent text-forest hover:bg-olive/10 border border-transparent disabled:opacity-50',
    danger:
      'bg-danger text-cornsilk hover:opacity-90 border border-danger shadow-xs disabled:opacity-50',
  }

  const sizeStyles: Record<NonNullable<ButtonProps['size']>, string> = {
    xs: 'px-2.5 py-1 text-xs rounded-md gap-1.5',
    sm: 'px-3 py-1.5 text-xs rounded-lg gap-1.5',
    md: 'px-4 py-2 text-sm rounded-lg gap-2',
    lg: 'px-5 py-2.5 text-sm rounded-xl gap-2.5',
  }

  return React.createElement(
    'button',
    {
      type,
      className: clsx(
        'inline-flex items-center justify-center font-medium transition-all duration-150 cursor-pointer disabled:cursor-not-allowed select-none',
        variantStyles[variant],
        sizeStyles[size],
        className
      ),
      ...props,
    },
    children
  )
}

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  hasError?: boolean
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ hasError, className, ...props }, ref) => {
    return React.createElement('input', {
      ref,
      className: clsx(
        'w-full rounded-lg border px-3 py-1.5 text-sm text-forest bg-cornsilk transition-colors focus:outline-none focus:ring-2',
        hasError
          ? 'border-danger focus:ring-danger/30 bg-danger-tint/40'
          : 'border-olive/35 focus:border-olive focus:ring-olive/25',
        className
      ),
      ...props,
    })
  }
)

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  hasError?: boolean
}

export function Select({ hasError, className, children, ...props }: SelectProps) {
  return React.createElement(
    'select',
    {
      className: clsx(
        'w-full rounded-lg border px-3 py-1.5 text-sm text-forest bg-cornsilk transition-colors focus:outline-none focus:ring-2 cursor-pointer',
        hasError
          ? 'border-danger focus:ring-danger/30'
          : 'border-olive/35 focus:border-olive focus:ring-olive/25',
        className
      ),
      ...props,
    },
    children
  )
}

export function Textarea({
  className,
  ...props
}: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return React.createElement('textarea', {
    className: clsx(
      'w-full rounded-lg border border-olive/35 bg-cornsilk px-3 py-2 text-xs font-mono text-forest focus:border-olive focus:outline-none focus:ring-2 focus:ring-olive/25',
      className
    ),
    ...props,
  })
}

export interface HeadingProps extends React.HTMLAttributes<HTMLHeadingElement> {
  level?: 1 | 2 | 3 | 4
}

export function Heading({ level = 2, className, children, ...props }: HeadingProps) {
  const tag = `h${level}`
  const defaultStyles: Record<number, string> = {
    1: 'font-display text-2xl font-bold tracking-tight text-forest',
    2: 'font-display text-lg font-bold tracking-tight text-forest',
    3: 'font-display text-base font-semibold text-forest',
    4: 'font-display text-sm font-semibold text-forest',
  }
  return React.createElement(
    tag,
    {
      className: clsx(defaultStyles[level], className),
      ...props,
    },
    children
  )
}

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'elevated' | 'forest' | 'caramel' | 'copper' | 'olive'
}

export function Card({ variant = 'default', className, children, ...props }: CardProps) {
  const variantMap: Record<NonNullable<CardProps['variant']>, string> = {
    default: 'bg-cornsilk-card border border-olive/25 text-forest shadow-xs',
    elevated: 'bg-cornsilk border border-olive/35 text-forest shadow-sm',
    forest: 'bg-forest border border-olive/40 text-cornsilk shadow-sm',
    caramel: 'bg-caramel-tint border border-caramel/60 text-forest shadow-xs',
    copper: 'bg-copper-tint border border-copper/50 text-forest shadow-xs',
    olive: 'bg-olive-tint border border-olive/40 text-forest shadow-xs',
  }
  return (
    <div className={clsx('rounded-xl', variantMap[variant], className)} {...props}>
      {children}
    </div>
  )
}

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  tone?: 'olive' | 'forest' | 'caramel' | 'copper' | 'danger' | 'neutral'
}

export function Badge({ tone = 'olive', className, children, ...props }: BadgeProps) {
  const toneMap: Record<NonNullable<BadgeProps['tone']>, string> = {
    olive: 'bg-olive/15 text-forest border-olive/35',
    forest: 'bg-forest text-cornsilk border-forest',
    caramel: 'bg-caramel/30 text-forest border-caramel',
    copper: 'bg-copper/20 text-copper-dark border-copper/45',
    danger: 'bg-danger/15 text-danger border-danger/40',
    neutral: 'bg-cornsilk-deep text-forest-muted border-olive/25',
  }
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium',
        toneMap[tone],
        className
      )}
      {...props}
    >
      {children}
    </span>
  )
}
