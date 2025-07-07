import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import { 
  Upload as UploadIcon, 
  FileText, 
  CheckCircle, 
  AlertCircle,
  X,
  Loader2
} from 'lucide-react'
import { useUploadStatement } from '../hooks/useStatements'
import { formatFileSize, validateFile } from '../utils/helpers'
import { clsx } from 'clsx'

export function Upload() {
  const [files, setFiles] = useState([])
  const navigate = useNavigate()
  const uploadMutation = useUploadStatement(navigate)

  const onDrop = (acceptedFiles, rejectedFiles) => {
    // Handle rejected files
    rejectedFiles.forEach(({ file, errors }) => {
      console.error(`File ${file.name} rejected:`, errors)
    })

    // Validate and add accepted files
    const validFiles = acceptedFiles.map(file => {
      const validation = validateFile(file)
      return {
        file,
        id: Math.random().toString(36).substr(2, 9),
        status: validation.isValid ? 'ready' : 'error',
        errors: validation.errors,
        progress: 0
      }
    })

    setFiles(prev => [...prev, ...validFiles])
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    maxSize: 50 * 1024 * 1024, // 50MB
    multiple: true
  })

  const removeFile = (id) => {
    setFiles(prev => prev.filter(f => f.id !== id))
  }

  const uploadFiles = async () => {
    const readyFiles = files.filter(f => f.status === 'ready')
    
    for (const fileItem of readyFiles) {
      try {
        // Update status to uploading
        setFiles(prev => prev.map(f => 
          f.id === fileItem.id 
            ? { ...f, status: 'uploading', progress: 50 }
            : f
        ))

        // Upload file
        const result = await uploadMutation.mutateAsync(fileItem.file)
        console.log('Upload result:', result)
        
        if (result && (result.statement_id || result.id)) {
          const statementId = result.statement_id || result.id
          
          // Update status to success with metadata
          setFiles(prev => prev.map(f => 
            f.id === fileItem.id 
              ? { 
                  ...f, 
                  status: 'success', 
                  progress: 100, 
                  statementId: statementId,
                  metadata: result
                }
              : f
          ))
          
          // Navigate to the statement detail page
          if (navigate && statementId) {
            navigate(`/statements/${statementId}`)
          }
        } else {
          throw new Error('No statement ID in response')
        }

      } catch (error) {
        // Update status to error
        const errorMessage = error.response?.data?.detail?.message || 
                           error.response?.data?.detail || 
                           error.message || 
                           'Error al subir el archivo'
        
        setFiles(prev => prev.map(f => 
          f.id === fileItem.id 
            ? { ...f, status: 'error', progress: 0, errors: [errorMessage] }
            : f
        ))
      }
    }
  }

  const readyFiles = files.filter(f => f.status === 'ready')
  const hasSuccessFiles = files.some(f => f.status === 'success')

  return (
    <div className="space-y-6">
      {/* Breadcrumb */}
      <nav className="flex" aria-label="Breadcrumb">
        <ol className="inline-flex items-center space-x-1 md:space-x-2 rtl:space-x-reverse">
          <li className="inline-flex items-center">
            <Link 
              to="/" 
              className="inline-flex items-center text-sm font-medium text-muted-foreground hover:text-primary"
            >
              <svg className="w-3 h-3 me-2.5" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 20 20">
                <path d="m19.707 9.293-2-2-7-7a1 1 0 0 0-1.414 0l-7 7-2 2a1 1 0 0 0 1.414 1.414L4 11.414V18a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1v-4a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v4a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1v-6.586l.293.293a1 1 0 0 0 1.414-1.414Z"/>
              </svg>
              Inicio
            </Link>
          </li>
          <li aria-current="page">
            <div className="flex items-center">
              <svg className="rtl:rotate-180 w-3 h-3 text-muted-foreground mx-1" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 6 10">
                <path stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="m1 9 4-4-4-4"/>
              </svg>
              <span className="ms-1 text-sm font-medium text-muted-foreground md:ms-2">
                Subir Estado de Cuenta
              </span>
            </div>
          </li>
        </ol>
      </nav>

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-foreground">Subir Estado de Cuenta</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Sube archivos PDF de estados de cuenta para analizarlos con IA
        </p>
      </div>

      {/* Upload Area */}
      <div className="bg-card shadow rounded-lg border border-border">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-card-foreground">Seleccionar Archivos</h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Arrastra archivos PDF aquí o haz clic para seleccionar
          </p>
        </div>

        <div className="p-6">
          <div
            {...getRootProps()}
            className={clsx(
              'dropzone',
              isDragActive && 'active',
              files.length > 0 && 'border-gray-300'
            )}
          >
            <input {...getInputProps()} />
            <div className="text-center">
              <UploadIcon className="mx-auto h-12 w-12 text-muted-foreground" />
              <div className="mt-4">
                {isDragActive ? (
                  <p className="text-lg text-primary-600">Suelta los archivos aquí...</p>
                ) : (
                  <>
                    <p className="text-lg text-foreground">
                      Arrastra archivos PDF aquí o{' '}
                      <span className="text-primary-600 font-medium">selecciona archivos</span>
                    </p>
                    <p className="mt-2 text-sm text-muted-foreground">
                      Máximo 50MB por archivo • Solo archivos PDF
                    </p>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* File List */}
          {files.length > 0 && (
            <div className="mt-6 space-y-3">
              <h4 className="text-sm font-medium text-foreground">
                Archivos seleccionados ({files.length})
              </h4>
              
              <div className="space-y-2">
                {files.map((fileItem) => (
                  <FileItem
                    key={fileItem.id}
                    fileItem={fileItem}
                    onRemove={() => removeFile(fileItem.id)}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Upload Button */}
          {readyFiles.length > 0 && (
            <div className="mt-6 flex justify-end space-x-3">
              <button
                onClick={() => setFiles([])}
                className="btn btn-secondary btn-md"
                disabled={uploadMutation.isPending}
              >
                Limpiar Todo
              </button>
              <button
                onClick={uploadFiles}
                disabled={uploadMutation.isPending || readyFiles.length === 0}
                className="btn btn-primary btn-md"
              >
                {uploadMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Subiendo...
                  </>
                ) : (
                  <>
                    <UploadIcon className="h-4 w-4 mr-2" />
                    Subir {readyFiles.length} archivo(s)
                  </>
                )}
              </button>
            </div>
          )}

          {/* Success Actions */}
          {hasSuccessFiles && (
            <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center">
                <CheckCircle className="h-5 w-5 text-success" />
                <h4 className="ml-2 text-sm font-medium text-success">
                  Archivos subidos correctamente
                </h4>
              </div>
              <p className="mt-2 text-sm text-success">
                Los archivos se han subido exitosamente. Ahora puedes procesarlos para obtener el análisis.
              </p>
              <div className="mt-4 flex space-x-3">
                <button
                  onClick={() => navigate('/statements')}
                  className="btn btn-success btn-sm"
                >
                  Ver Estados de Cuenta
                </button>
                <button
                  onClick={() => setFiles([])}
                  className="btn btn-secondary btn-sm"
                >
                  Subir Más Archivos
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Instructions */}
      <div className="bg-primary/10 border border-primary/20 rounded-lg p-6">
        <h4 className="text-sm font-medium text-primary mb-3">💡 Instrucciones</h4>
        <ul className="space-y-2 text-sm text-primary">
          <li className="flex items-start">
            <span className="flex-shrink-0 w-1.5 h-1.5 bg-primary rounded-full mt-2 mr-3"></span>
            Solo se aceptan archivos PDF del formato CONDUSEF universal (desde octubre 2024)
          </li>
          <li className="flex items-start">
            <span className="flex-shrink-0 w-1.5 h-1.5 bg-primary rounded-full mt-2 mr-3"></span>
            Puedes subir múltiples archivos de diferentes meses
          </li>
          <li className="flex items-start">
            <span className="flex-shrink-0 w-1.5 h-1.5 bg-primary rounded-full mt-2 mr-3"></span>
            Los archivos se procesan localmente y no se envían a servicios externos
          </li>
          <li className="flex items-start">
            <span className="flex-shrink-0 w-1.5 h-1.5 bg-primary rounded-full mt-2 mr-3"></span>
            Después de subir, usa el botón "Procesar" para analizar las transacciones
          </li>
        </ul>
      </div>
    </div>
  )

  function FileItem({ fileItem, onRemove }) {
    const { file, status, progress, errors = [], metadata, statementId } = fileItem
    
    const statusInfo = {
      ready: { text: 'Listo para subir', icon: FileText, color: 'text-muted-foreground' },
      uploading: { text: 'Subiendo...', icon: Loader2, color: 'text-primary animate-spin' },
      success: { text: 'Subido correctamente', icon: CheckCircle, color: 'text-success' },
      error: { text: 'Error al subir', icon: AlertCircle, color: 'text-destructive' },
    }[status] || { text: 'Desconocido', icon: FileText, color: 'text-muted-foreground' }
    
    return (
      <div className="flex flex-col p-3 bg-muted/50 rounded-lg space-y-2">
        <div className="flex items-center justify-between w-full">
          <div className="flex items-center space-x-3 min-w-0 flex-1">
            <div className={`p-2 rounded-full ${statusInfo.color.replace('text-', 'bg-')} bg-opacity-10`}>
              <statusInfo.icon className={`h-5 w-5 ${statusInfo.color}`} />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-foreground truncate">{file.name}</p>
              <p className="text-xs text-muted-foreground">
                {formatFileSize(file.size)} • {statusInfo.text}
              </p>
            </div>
          </div>
          
          {status === 'uploading' ? (
            <div className="w-24 bg-muted rounded-full h-2">
              <div 
                className="bg-primary h-2 rounded-full transition-all duration-300" 
                style={{ width: `${progress}%` }}
              />
            </div>
          ) : (
            <button
              onClick={() => onRemove(fileItem.id)}
              className="text-muted-foreground hover:text-foreground flex-shrink-0 ml-2"
            >
              <X className="h-5 w-5" />
            </button>
          )}
        </div>
        
        {/* Metadata for successful uploads */}
        {status === 'success' && metadata && (
          <div className="bg-card border border-border rounded-md p-3 text-sm mt-1">
            <div className="grid grid-cols-2 gap-2">
              {metadata.bank_name && (
                <div>
                  <p className="text-xs text-muted-foreground">Banco</p>
                  <p className="font-medium">{metadata.bank_name}</p>
                </div>
              )}
              {metadata.statement_period && (
                <div>
                  <p className="text-xs text-muted-foreground">Período</p>
                  <p className="font-medium">{metadata.statement_period}</p>
                </div>
              )}
            </div>
            {statementId && (
              <p className="mt-2 text-xs text-success">
                ID: {String(statementId).slice(0, 8)}...
              </p>
            )}
          </div>
        )}
        
        {/* Error messages */}
        {errors.length > 0 && (
          <div className="mt-1 text-sm text-destructive bg-destructive/10 p-2 rounded-md">
            {errors[0]}
          </div>
        )}
      </div>
    )
  }
}