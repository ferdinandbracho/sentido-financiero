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
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      console.log('Sending upload request...')
      const response = await api.post('/statements/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      
      console.log('Upload response received:', response.data)
      
      // Normalize the response format
      const data = response.data;
      return {
        ...data,
        // Ensure we always have a statement_id field, even if it's called 'id' in the response
        statement_id: data.statement_id || data.id,
        // Include the raw response for debugging
        _raw: data
      };
    } catch (error) {
      console.error('Upload error:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
        headers: error.response?.headers,
      });
      
      // Rethrow with a more descriptive error
      const errorMessage = error.response?.data?.detail || 
                         error.response?.data?.message || 
                         error.message || 
                         'Failed to upload statement';
      
      const err = new Error(errorMessage);
      err.response = error.response;
      throw err;
    }
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

  // Bulk delete statements
  bulkDelete: async (statementIds) => {
    const response = await api.post('/statements/bulk-delete', {
      statement_ids: statementIds
    })
    return response.data
  },

  // Bulk download statements
  bulkDownload: async (statementIds) => {
    const response = await api.post('/statements/bulk-download', {
      statement_ids: statementIds
    }, {
      responseType: 'blob'
    })
    
    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    
    // Get filename from Content-Disposition header or use default
    const contentDisposition = response.headers['content-disposition']
    let filename = 'statements_export.csv'
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename=(.+)/)
      if (filenameMatch) {
        filename = filenameMatch[1].replace(/['"]/g, '')
      }
    }
    
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
    
    return { success: true, filename }
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