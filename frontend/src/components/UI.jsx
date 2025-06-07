import { useState } from 'react'
import { clsx } from 'clsx'

/**
 * Loading Spinner Component
 */
export function LoadingSpinner({ size = 'md', className }) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8',
    xl: 'h-12 w-12'
  }

  return (
    <div className={clsx(
      'animate-spin rounded-full border-2 border-gray-300 border-t-primary-600',
      sizeClasses[size],
      className
    )} />
  )
}

/**
 * Loading Skeleton Component
 */
export function LoadingSkeleton({ className, ...props }) {
  return (
    <div
      className={clsx(
        'animate-pulse bg-gray-200 rounded',
        className
      )}
      {...props}
    />
  )
}

/**
 * Empty State Component
 */
export function EmptyState({ 
  icon: Icon, 
  title, 
  description, 
  action,
  className 
}) {
  return (
    <div className={clsx('text-center py-12', className)}>
      {Icon && (
        <Icon className="mx-auto h-12 w-12 text-gray-400" />
      )}
      <h3 className="mt-2 text-sm font-medium text-gray-900">
        {title}
      </h3>
      {description && (
        <p className="mt-1 text-sm text-gray-500">
          {description}
        </p>
      )}
      {action && (
        <div className="mt-6">
          {action}
        </div>
      )}
    </div>
  )
}

/**
 * Alert Component
 */
export function Alert({ 
  type = 'info', 
  title, 
  children, 
  onClose,
  className 
}) {
  const typeClasses = {
    info: 'bg-blue-50 border-blue-200 text-blue-800',
    success: 'bg-green-50 border-green-200 text-green-800',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    error: 'bg-red-50 border-red-200 text-red-800'
  }

  const iconClasses = {
    info: 'text-blue-400',
    success: 'text-green-400',
    warning: 'text-yellow-400',
    error: 'text-red-400'
  }

  return (
    <div className={clsx(
      'rounded-md border p-4',
      typeClasses[type],
      className
    )}>
      <div className="flex">
        <div className="flex-shrink-0">
          {/* Add icons based on type */}
        </div>
        <div className="ml-3 flex-1">
          {title && (
            <h3 className="text-sm font-medium">
              {title}
            </h3>
          )}
          <div className={clsx(title ? 'mt-2' : '', 'text-sm')}>
            {children}
          </div>
        </div>
        {onClose && (
          <div className="ml-auto pl-3">
            <button
              onClick={onClose}
              className="inline-flex rounded-md p-1.5 hover:bg-black/5 focus:outline-none focus:ring-2 focus:ring-offset-2"
            >
              <span className="sr-only">Cerrar</span>
              ×
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * Modal Component
 */
export function Modal({ 
  isOpen, 
  onClose, 
  title, 
  children, 
  size = 'md',
  showCloseButton = true 
}) {
  if (!isOpen) return null

  const sizeClasses = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl'
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        {/* Backdrop */}
        <div 
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          onClick={onClose}
        />

        {/* Modal */}
        <div className={clsx(
          'inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle w-full',
          sizeClasses[size]
        )}>
          {title && (
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">
                  {title}
                </h3>
                {showCloseButton && (
                  <button
                    onClick={onClose}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    ×
                  </button>
                )}
              </div>
            </div>
          )}
          <div className="px-6 py-4">
            {children}
          </div>
        </div>
      </div>
    </div>
  )
}

/**
 * Tooltip Component
 */
export function Tooltip({ children, content, position = 'top' }) {
  const [isVisible, setIsVisible] = useState(false)

  const positionClasses = {
    top: 'bottom-full left-1/2 transform -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 transform -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 transform -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 transform -translate-y-1/2 ml-2'
  }

  return (
    <div 
      className="relative inline-block"
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      {children}
      {isVisible && (
        <div className={clsx(
          'absolute z-10 px-2 py-1 text-xs text-white bg-gray-900 rounded whitespace-nowrap',
          positionClasses[position]
        )}>
          {content}
        </div>
      )}
    </div>
  )
}

/**
 * Badge Component
 */
export function Badge({ children, variant = 'default', size = 'md' }) {
  const variantClasses = {
    default: 'bg-gray-100 text-gray-800',
    primary: 'bg-primary-100 text-primary-800',
    success: 'bg-green-100 text-green-800',
    warning: 'bg-yellow-100 text-yellow-800',
    error: 'bg-red-100 text-red-800'
  }

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-0.5 text-xs',
    lg: 'px-3 py-1 text-sm'
  }

  return (
    <span className={clsx(
      'inline-flex items-center rounded-full font-medium',
      variantClasses[variant],
      sizeClasses[size]
    )}>
      {children}
    </span>
  )
}