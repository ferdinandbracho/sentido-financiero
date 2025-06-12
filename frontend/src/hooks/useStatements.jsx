import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { statementsAPI } from '../services/api'
import toast from 'react-hot-toast'
import { AlertTriangle } from 'lucide-react'

// Query keys
export const QUERY_KEYS = {
  statements: 'statements',
  statement: (id) => ['statement', id],
  transactions: (id) => ['transactions', id],
  analysis: (id) => ['analysis', id],
}

/**
 * Hook for fetching all statements
 */
export const useStatements = (params = {}) => {
  return useQuery({
    queryKey: [QUERY_KEYS.statements, params],
    queryFn: async () => {
      const data = await statementsAPI.getAll(params);
      return data.statements || [];
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

/**
 * Hook for fetching a single statement
 */
export const useStatement = (id) => {
  return useQuery({
    queryKey: QUERY_KEYS.statement(id),
    queryFn: () => statementsAPI.getById(id),
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
  })
}

/**
 * Hook for fetching statement transactions
 */
export const useTransactions = (id, params = {}) => {
  return useQuery({
    queryKey: [...QUERY_KEYS.transactions(id), params],
    queryFn: () => statementsAPI.getTransactions(id, params),
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
  })
}

/**
 * Hook for fetching statement analysis
 */
export const useAnalysis = (id) => {
  return useQuery({
    queryKey: QUERY_KEYS.analysis(id),
    queryFn: () => statementsAPI.getAnalysis(id),
    enabled: !!id,
    staleTime: 10 * 60 * 1000, // 10 minutes for analysis
  })
}

/**
 * Hook for uploading files
 */
export const useUploadStatement = (navigate) => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: statementsAPI.upload,
    onSuccess: (data) => {
      if (data.is_duplicate) {
        // This is a duplicate, show warning and navigate to existing statement
        toast.custom((t) => (
          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <AlertTriangle className="h-5 w-5 text-yellow-400" aria-hidden="true" />
              </div>
              <div className="ml-3">
                <p className="text-sm text-yellow-700">{data.message}</p>
                <div className="mt-2">
                  <button
                    type="button"
                    className="rounded-md bg-yellow-50 px-2 py-1.5 text-sm font-medium text-yellow-800 hover:bg-yellow-100 focus:outline-none focus:ring-2 focus:ring-yellow-600 focus:ring-offset-2 focus:ring-offset-yellow-50"
                    onClick={() => {
                      navigate(`/statements/${data.statement_id}`)
                      toast.dismiss(t.id)
                    }}
                  >
                    Ver estado de cuenta existente
                  </button>
                </div>
              </div>
            </div>
          </div>
        ), { duration: 10000 })
      } else {
        // New file uploaded successfully
        toast.success(data.message || 'Archivo subido correctamente')
        
        // Manually add the newly uploaded statement to the cache with complete metadata
        // This ensures the statement appears in the list immediately with all metadata
        const newStatement = {
          id: data.statement_id,
          filename: data.filename,
          bank_name: data.metadata?.bank_name || 'Desconocido',
          file_size: data.file_size,
          upload_date: new Date().toISOString(),
          processing_status: data.status || 'uploaded'
        }
        
        // Update the query cache with the new statement
        const existingStatements = queryClient.getQueryData([QUERY_KEYS.statements]) || []
        queryClient.setQueryData([QUERY_KEYS.statements], [...existingStatements, newStatement])
      }
      
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.statements] })
      return data
    },
    onError: (error) => {
      // Handle duplicate statement error
      if (error.response?.status === 409) {
        const { message, statement_id } = error.response.data.detail || {}
        toast.custom((t) => (
          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <AlertTriangle className="h-5 w-5 text-yellow-400" aria-hidden="true" />
              </div>
              <div className="ml-3">
                <p className="text-sm text-yellow-700">{message}</p>
                <div className="mt-2">
                  <button
                    type="button"
                    className="rounded-md bg-yellow-50 px-2 py-1.5 text-sm font-medium text-yellow-800 hover:bg-yellow-100 focus:outline-none focus:ring-2 focus:ring-yellow-600 focus:ring-offset-2 focus:ring-offset-yellow-50"
                    onClick={() => {
                      navigate(`/statements/${statement_id}`)
                      toast.dismiss(t.id)
                    }}
                  >
                    Ver estado de cuenta existente
                  </button>
                </div>
              </div>
            </div>
          </div>
        ), { duration: 10000 })
      } else {
        // Other errors
        const message = error.response?.data?.detail?.message || 
                      error.response?.data?.detail || 
                      'Error al subir el archivo'
        toast.error(message)
      }
      throw error
    },
  })
}

/**
 * Hook for processing statements
 */
export const useProcessStatement = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: statementsAPI.process,
    onSuccess: (data, variables) => {
      toast.success('Procesamiento iniciado')
      // Invalidate the specific statement to update its status
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.statement(variables) })
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.statements] })
      return data
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Error al procesar el archivo'
      toast.error(message)
      throw error
    },
  })
}

/**
 * Hook for deleting statements
 */
export const useDeleteStatement = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: statementsAPI.delete,
    onSuccess: (data, variables) => {
      toast.success('Estado de cuenta eliminado')
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.statements] })
      // Remove the specific statement from cache
      queryClient.removeQueries({ queryKey: QUERY_KEYS.statement(variables) })
      queryClient.removeQueries({ queryKey: QUERY_KEYS.transactions(variables) })
      queryClient.removeQueries({ queryKey: QUERY_KEYS.analysis(variables) })
      return data
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Error al eliminar el archivo'
      toast.error(message)
      throw error
    },
  })
}