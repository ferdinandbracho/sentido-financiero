import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`)
    return response
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

// Statements API
export const statementsAPI = {
  // Upload a PDF file
  upload: async (file) => {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await api.post('/statements/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  // Get all statements
  getAll: async (params = {}) => {
    const response = await api.get('/statements/', { params })
    return response.data
  },

  // Get statement by ID
  getById: async (id) => {
    const response = await api.get(`/statements/${id}`)
    return response.data
  },

  // Process a statement
  process: async (id) => {
    const response = await api.post(`/statements/${id}/process`)
    return response.data
  },

  // Get statement transactions
  getTransactions: async (id, params = {}) => {
    const response = await api.get(`/statements/${id}/transactions`, { params })
    return response.data
  },

  // Get statement analysis
  getAnalysis: async (id) => {
    const response = await api.get(`/statements/${id}/analysis`)
    return response.data
  },

  // Delete statement
  delete: async (id) => {
    const response = await api.delete(`/statements/${id}`)
    return response.data
  },
}

// Transactions API
export const transactionsAPI = {
  // Get transaction by ID
  getById: async (id) => {
    const response = await api.get(`/transactions/${id}/`)
    return response.data
  },

  // Update transaction
  update: async (id, data) => {
    const response = await api.put(`/transactions/${id}/`, data)
    return response.data
  },

  // Delete transaction
  delete: async (id) => {
    const response = await api.delete(`/transactions/${id}/`)
    return response.data
  },
}

// Health API
export const healthAPI = {
  // Check API health
  check: async () => {
    const response = await api.get('/health/health-check/')
    return response.data
  },
}

export default api