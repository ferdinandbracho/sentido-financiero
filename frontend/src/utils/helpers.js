/**
 * Format currency amounts
 */
export const formatCurrency = (amount, currency = 'MXN') => {
  if (amount == null || isNaN(amount)) return '$0.00'
  
  return new Intl.NumberFormat('es-MX', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Math.abs(amount))
}

/**
 * Format percentage
 */
export const formatPercentage = (value, decimals = 1) => {
  if (value == null || isNaN(value)) return '0%'
  return `${value > 0 ? '+' : ''}${value.toFixed(decimals)}%`
}

/**
 * Format file size
 */
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * Format date for display
 */
export const formatDate = (date, format = 'short') => {
  if (!date) return ''
  
  const dateObj = typeof date === 'string' ? new Date(date) : date
  
  if (format === 'short') {
    return dateObj.toLocaleDateString('es-MX', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }
  
  if (format === 'long') {
    return dateObj.toLocaleDateString('es-MX', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }
  
  if (format === 'relative') {
    const now = new Date()
    const diff = now - dateObj
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))
    
    // Handle invalid or future dates
    if (isNaN(days) || days < 0) return 'Recientemente'
    
    if (days === 0) return 'Hoy'
    if (days === 1) return 'Ayer'
    if (days < 7) return `Hace ${days} días`
    if (days < 30) return `Hace ${Math.floor(days / 7)} semanas`
    if (days < 365) return `Hace ${Math.floor(days / 30)} meses`
    return `Hace ${Math.floor(days / 365)} años`
  }
  
  return dateObj.toLocaleDateString('es-MX')
}

/**
 * Capitalize first letter
 */
export const capitalize = (str) => {
  if (!str) return ''
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase()
}

/**
 * Get category display name and color
 */
export const getCategoryInfo = (category) => {
  const categoryMap = {
    alimentacion: {
      name: 'Alimentación',
      color: 'bg-green-100 text-green-800',
      icon: '🍽️'
    },
    gasolineras: {
      name: 'Gasolineras',
      color: 'bg-yellow-100 text-yellow-800',
      icon: '⛽'
    },
    servicios: {
      name: 'Servicios',
      color: 'bg-blue-100 text-blue-800',
      icon: '🔧'
    },
    salud: {
      name: 'Salud',
      color: 'bg-red-100 text-red-800',
      icon: '🏥'
    },
    transporte: {
      name: 'Transporte',
      color: 'bg-purple-100 text-purple-800',
      icon: '🚗'
    },
    entretenimiento: {
      name: 'Entretenimiento',
      color: 'bg-pink-100 text-pink-800',
      icon: '🎬'
    },
    ropa: {
      name: 'Ropa',
      color: 'bg-indigo-100 text-indigo-800',
      icon: '👕'
    },
    educacion: {
      name: 'Educación',
      color: 'bg-orange-100 text-orange-800',
      icon: '📚'
    },
    transferencias: {
      name: 'Transferencias',
      color: 'bg-gray-100 text-gray-800',
      icon: '💸'
    },
    seguros: {
      name: 'Seguros',
      color: 'bg-teal-100 text-teal-800',
      icon: '🛡️'
    },
    intereses_comisiones: {
      name: 'Intereses/Comisiones',
      color: 'bg-red-100 text-red-800',
      icon: '📊'
    },
    otros: {
      name: 'Otros',
      color: 'bg-gray-100 text-gray-800',
      icon: '📋'
    }
  }
  
  return categoryMap[category] || categoryMap.otros
}

/**
 * Get processing status info
 */
export const getStatusInfo = (status) => {
  const statusMap = {
    uploaded: {
      name: 'Subido',
      color: 'bg-blue-100 text-blue-800',
      icon: '📄'
    },
    processing: {
      name: 'Procesando',
      color: 'bg-yellow-100 text-yellow-800',
      icon: '⏳'
    },
    processed: {
      name: 'Procesado',
      color: 'bg-green-100 text-green-800',
      icon: '✅'
    },
    failed: {
      name: 'Error',
      color: 'bg-red-100 text-red-800',
      icon: '❌'
    }
  }
  
  return statusMap[status] || statusMap.uploaded
}

/**
 * Debounce function
 */
export const debounce = (func, wait) => {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

/**
 * Generate chart colors
 */
export const generateColors = (count) => {
  const colors = [
    '#3b82f6', // blue
    '#10b981', // emerald  
    '#f59e0b', // amber
    '#ef4444', // red
    '#8b5cf6', // violet
    '#06b6d4', // cyan
    '#84cc16', // lime
    '#f97316', // orange
    '#ec4899', // pink
    '#6b7280', // gray
  ]
  
  const result = []
  for (let i = 0; i < count; i++) {
    result.push(colors[i % colors.length])
  }
  return result
}

/**
 * Download data as file
 */
export const downloadAsFile = (data, filename, type = 'application/json') => {
  const blob = new Blob([data], { type })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

/**
 * Validate file type and size
 */
export const validateFile = (file, maxSize = 50 * 1024 * 1024) => {
  const errors = []
  
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    errors.push('Solo se permiten archivos PDF')
  }
  
  if (file.size > maxSize) {
    errors.push(`El archivo debe ser menor a ${formatFileSize(maxSize)}`)
  }
  
  return {
    isValid: errors.length === 0,
    errors
  }
}

/**
 * Calculate confidence level description
 */
export const getConfidenceDescription = (confidence) => {
  if (confidence >= 0.9) return 'Muy alta'
  if (confidence >= 0.7) return 'Alta'
  if (confidence >= 0.5) return 'Media'
  if (confidence >= 0.3) return 'Baja'
  return 'Muy baja'
}

/**
 * Format statement filename for display
 * 
 * Transforms raw filenames like "bbva_202506_statement.pdf" into
 * user-friendly display names like "BBVA - Junio 2025"
 */
export const formatStatementName = (statement) => {
  // Guard clause: if statement is null or undefined, return fallback
  if (!statement) {
    return 'Estado de Cuenta'
  }
  
  // If the filename is already in the auto-renamed format "BANK - Month Year", return it as is
  if (statement.filename && statement.filename.match(/^[A-Z]+ - [A-Za-z]+ \d{4}$/)) {
    return statement.filename
  }
  
  // If we have bank name and statement period, use those
  if (statement.bank_name && statement.statement_period_start) {
    const date = new Date(statement.statement_period_start)
    const month = date.toLocaleString('es-MX', { month: 'long' })
    const year = date.getFullYear()
    return `${statement.bank_name} - ${capitalize(month)} ${year}`
  }
  
  // Try to parse from filename if in the format bank_YYYYMM_originalname.pdf
  if (!statement.filename) {
    return 'Estado de Cuenta Sin Nombre'
  }
  
  const filenameMatch = statement.filename.match(/^([a-z_]+)_(\d{6})_.*\.pdf$/i)
  if (filenameMatch) {
    const [, bankSlug, yearMonth] = filenameMatch
    const year = yearMonth.substring(0, 4)
    const month = yearMonth.substring(4, 6)
    const date = new Date(parseInt(year), parseInt(month) - 1, 1)
    const monthName = date.toLocaleString('es-MX', { month: 'long' })
    const bankName = bankSlug.split('_').map(capitalize).join(' ')
    return `${bankName} - ${capitalize(monthName)} ${year}`
  }
  
  // Fallback to original filename (remove .pdf extension if present)
  const displayName = statement.filename.replace(/\.pdf$/i, '')
  return displayName
}