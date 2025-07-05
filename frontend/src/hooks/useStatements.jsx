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
    queryFn: async () => {
      if (!id || id === 'undefined') {
        throw new Error('Invalid statement ID')
      }
      return await statementsAPI.getById(id)
    },
    enabled: !!id && id !== 'undefined',
    staleTime: 5 * 60 * 1000,
    retry: (failureCount, error) => {
      // Don't retry if the error is due to invalid ID
      if (error.message === 'Invalid statement ID') {
        return false
      }
      // Retry up to 3 times for other errors
      return failureCount < 3
    },
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
    mutationFn: async (file) => {
      const response = await statementsAPI.upload(file);
      console.log('Upload response:', response);
      
      // Ensure we have a valid statement ID in the response
      if (!response.statement_id && !response.id) {
        console.error('No statement ID in upload response:', response);
        throw new Error('No statement ID received from server');
      }
      
      // Normalize the response to always use statement_id
      const normalizedResponse = {
        ...response,
        statement_id: response.statement_id || response.id
      };
      
      console.log('Normalized upload response:', normalizedResponse);
      return normalizedResponse;
    },
    onSuccess: (data) => {
      console.log('Upload success data:', data);
      
      // Ensure we have a valid statement ID before proceeding
      const statementId = data.statement_id;
      if (!statementId) {
        console.error('No statement ID in success data:', data);
        toast.error('Error: No se pudo obtener el ID del estado de cuenta');
        return;
      }
      
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
                      // Use the normalized statementId
                      navigate(`/statements/${statementId}`);
                      toast.dismiss(t.id);
                    }}
                  >
                    Ver estado de cuenta existente
                  </button>
                </div>
              </div>
            </div>
          </div>
        ), { duration: 10000 });
      } else {
        // New file uploaded successfully
        toast.success(data.message || 'Archivo subido correctamente');
        
        // Manually add the newly uploaded statement to the cache with complete metadata
        // This ensures the statement appears in the list immediately with all metadata
        const newStatement = {
          id: statementId,
          filename: data.filename,
          bank_name: data.metadata?.bank_name || 'Desconocido',
          file_size: data.file_size,
          upload_date: new Date().toISOString(),
          processing_status: data.status || 'uploaded'
        };
        
        // Update the query cache with the new statement
        const existingStatements = queryClient.getQueryData([QUERY_KEYS.statements]) || [];
        queryClient.setQueryData([QUERY_KEYS.statements], [...existingStatements, newStatement]);
        
        // Navigate to the new statement detail page
        navigate(`/statements/${statementId}`);
      }
      
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.statements] })
      return data
    },
    onError: (error) => {
      // Handle duplicate statement error
      if (error.response?.status === 409) {
        const detail = error.response.data.detail || {}
        const { message, existing_statement_id, formatted_name } = detail
        toast.custom((t) => (
          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <AlertTriangle className="h-5 w-5 text-yellow-400" aria-hidden="true" />
              </div>
              <div className="ml-3">
                <p className="text-sm text-yellow-700">
                  {message || 'Este estado de cuenta ya existe'}
                </p>
                {formatted_name && (
                  <p className="text-xs text-yellow-600 mt-1">
                    {formatted_name}
                  </p>
                )}
                <div className="mt-2">
                  <button
                    type="button"
                    className="rounded-md bg-yellow-50 px-2 py-1.5 text-sm font-medium text-yellow-800 hover:bg-yellow-100 focus:outline-none focus:ring-2 focus:ring-yellow-600 focus:ring-offset-2 focus:ring-offset-yellow-50"
                    onClick={() => {
                      navigate(`/statements/${existing_statement_id}`)
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
                      error.message || 
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

/**
 * Hook for bulk deleting statements
 */
export const useBulkDeleteStatements = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: statementsAPI.bulkDelete,
    onSuccess: (data) => {
      const { processed_count, failed_count, message } = data
      
      if (processed_count > 0) {
        toast.success(message || `${processed_count} estados de cuenta eliminados`)
      }
      
      if (failed_count > 0) {
        toast.error(`No se pudieron eliminar ${failed_count} estados de cuenta`)
      }
      
      // Refresh the statements list
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.statements] })
      
      return data
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Error en eliminación masiva'
      toast.error(message)
      throw error
    },
  })
}

/**
 * Hook for bulk downloading statements
 */
export const useBulkDownloadStatements = () => {
  return useMutation({
    mutationFn: statementsAPI.bulkDownload,
    onSuccess: (data) => {
      toast.success(`Descarga iniciada: ${data.filename}`)
      return data
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Error en descarga masiva'
      toast.error(message)
      throw error
    },
  })
}