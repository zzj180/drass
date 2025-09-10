import { useState, useCallback, useRef } from 'react';
import axios, { AxiosProgressEvent, CancelTokenSource } from 'axios';
import { validateFiles, formatFileSize } from '../FileValidator';

export interface UploadFile {
  id: string;
  file: File;
  name: string;
  size: number;
  type: string;
  status: 'pending' | 'uploading' | 'success' | 'error' | 'cancelled';
  progress: number;
  error?: string;
  url?: string;
  uploadedAt?: Date;
}

interface UseFileUploadOptions {
  endpoint?: string;
  maxFiles?: number;
  maxSize?: number;
  maxTotalSize?: number;
  allowedTypes?: string[];
  autoUpload?: boolean;
  onSuccess?: (file: UploadFile) => void;
  onError?: (file: UploadFile, error: Error) => void;
  onProgress?: (file: UploadFile, progress: number) => void;
}

interface UseFileUploadReturn {
  files: UploadFile[];
  isUploading: boolean;
  totalProgress: number;
  addFiles: (newFiles: File[]) => void;
  removeFile: (id: string) => void;
  uploadFile: (id: string) => Promise<void>;
  uploadAll: () => Promise<void>;
  cancelUpload: (id: string) => void;
  cancelAll: () => void;
  clearAll: () => void;
  retryFailed: () => void;
}

/**
 * Custom hook for managing file uploads
 */
export const useFileUpload = (
  options: UseFileUploadOptions = {}
): UseFileUploadReturn => {
  const {
    endpoint = '/api/v1/documents/upload',
    maxFiles = 10,
    maxSize = 10 * 1024 * 1024,
    maxTotalSize = 50 * 1024 * 1024,
    allowedTypes,
    autoUpload = false,
    onSuccess,
    onError,
    onProgress,
  } = options;

  const [files, setFiles] = useState<UploadFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const cancelTokensRef = useRef<Map<string, CancelTokenSource>>(new Map());

  // Calculate total progress
  const totalProgress = files.length > 0
    ? files.reduce((sum, file) => sum + file.progress, 0) / files.length
    : 0;

  // Generate unique file ID
  const generateFileId = useCallback((file: File): string => {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}-${file.name}`;
  }, []);

  // Add files to upload queue
  const addFiles = useCallback((newFiles: File[]) => {
    // Validate files
    const validation = validateFiles(newFiles, {
      maxSize,
      maxFiles: maxFiles - files.length,
      maxTotalSize,
      allowedTypes,
    });

    // Create upload file objects
    const uploadFiles: UploadFile[] = validation.valid.map(file => ({
      id: generateFileId(file),
      file,
      name: file.name,
      size: file.size,
      type: file.type,
      status: 'pending' as const,
      progress: 0,
    }));

    // Add error files
    const errorFiles: UploadFile[] = validation.invalid.map(({ file, error }) => ({
      id: generateFileId(file),
      file,
      name: file.name,
      size: file.size,
      type: file.type,
      status: 'error' as const,
      progress: 0,
      error,
    }));

    setFiles(prev => [...prev, ...uploadFiles, ...errorFiles]);

    // Auto upload if enabled
    if (autoUpload && uploadFiles.length > 0) {
      uploadFiles.forEach(file => {
        uploadFile(file.id);
      });
    }

    // Log warnings
    if (validation.warnings.length > 0) {
      console.warn('File upload warnings:', validation.warnings);
    }
  }, [files.length, maxFiles, maxSize, maxTotalSize, allowedTypes, autoUpload, generateFileId]);

  // Remove file from list
  const removeFile = useCallback((id: string) => {
    // Cancel upload if in progress
    const cancelToken = cancelTokensRef.current.get(id);
    if (cancelToken) {
      cancelToken.cancel('Upload cancelled by user');
      cancelTokensRef.current.delete(id);
    }

    setFiles(prev => prev.filter(file => file.id !== id));
  }, []);

  // Upload single file
  const uploadFile = useCallback(async (id: string) => {
    const fileObj = files.find(f => f.id === id);
    if (!fileObj || fileObj.status === 'success') {
      return;
    }

    // Create cancel token
    const cancelToken = axios.CancelToken.source();
    cancelTokensRef.current.set(id, cancelToken);

    // Update status to uploading
    setFiles(prev => prev.map(f => 
      f.id === id ? { ...f, status: 'uploading' as const, progress: 0 } : f
    ));

    setIsUploading(true);

    try {
      // Create form data
      const formData = new FormData();
      formData.append('file', fileObj.file);
      formData.append('name', fileObj.name);
      formData.append('type', fileObj.type);

      // Upload file
      const response = await axios.post(endpoint, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        cancelToken: cancelToken.token,
        onUploadProgress: (progressEvent: AxiosProgressEvent) => {
          const progress = progressEvent.total
            ? Math.round((progressEvent.loaded * 100) / progressEvent.total)
            : 0;

          setFiles(prev => prev.map(f => 
            f.id === id ? { ...f, progress } : f
          ));

          onProgress?.(fileObj, progress);
        },
      });

      // Update file status on success
      const updatedFile: UploadFile = {
        ...fileObj,
        status: 'success',
        progress: 100,
        url: response.data.url,
        uploadedAt: new Date(),
      };

      setFiles(prev => prev.map(f => 
        f.id === id ? updatedFile : f
      ));

      onSuccess?.(updatedFile);
    } catch (error) {
      if (axios.isCancel(error)) {
        // Update status to cancelled
        setFiles(prev => prev.map(f => 
          f.id === id ? { ...f, status: 'cancelled' as const } : f
        ));
      } else {
        // Update status to error
        const errorMessage = error instanceof Error ? error.message : 'Upload failed';
        
        setFiles(prev => prev.map(f => 
          f.id === id ? { ...f, status: 'error' as const, error: errorMessage } : f
        ));

        onError?.(fileObj, error as Error);
      }
    } finally {
      cancelTokensRef.current.delete(id);
      
      // Check if any files are still uploading
      setFiles(prev => {
        const stillUploading = prev.some(f => f.status === 'uploading');
        if (!stillUploading) {
          setIsUploading(false);
        }
        return prev;
      });
    }
  }, [files, endpoint, onSuccess, onError, onProgress]);

  // Upload all pending files
  const uploadAll = useCallback(async () => {
    const pendingFiles = files.filter(f => f.status === 'pending');
    
    if (pendingFiles.length === 0) {
      return;
    }

    setIsUploading(true);

    // Upload files in parallel with concurrency limit
    const concurrency = 3;
    const chunks = [];
    
    for (let i = 0; i < pendingFiles.length; i += concurrency) {
      chunks.push(pendingFiles.slice(i, i + concurrency));
    }

    for (const chunk of chunks) {
      await Promise.all(chunk.map(file => uploadFile(file.id)));
    }

    setIsUploading(false);
  }, [files, uploadFile]);

  // Cancel single upload
  const cancelUpload = useCallback((id: string) => {
    const cancelToken = cancelTokensRef.current.get(id);
    if (cancelToken) {
      cancelToken.cancel('Upload cancelled by user');
      cancelTokensRef.current.delete(id);
    }
  }, []);

  // Cancel all uploads
  const cancelAll = useCallback(() => {
    cancelTokensRef.current.forEach(cancelToken => {
      cancelToken.cancel('All uploads cancelled');
    });
    cancelTokensRef.current.clear();

    setFiles(prev => prev.map(f => 
      f.status === 'uploading' 
        ? { ...f, status: 'cancelled' as const }
        : f
    ));

    setIsUploading(false);
  }, []);

  // Clear all files
  const clearAll = useCallback(() => {
    cancelAll();
    setFiles([]);
  }, [cancelAll]);

  // Retry failed uploads
  const retryFailed = useCallback(() => {
    const failedFiles = files.filter(f => f.status === 'error' || f.status === 'cancelled');
    
    failedFiles.forEach(file => {
      setFiles(prev => prev.map(f => 
        f.id === file.id ? { ...f, status: 'pending' as const, progress: 0, error: undefined } : f
      ));
      
      if (autoUpload) {
        uploadFile(file.id);
      }
    });
  }, [files, autoUpload, uploadFile]);

  return {
    files,
    isUploading,
    totalProgress,
    addFiles,
    removeFile,
    uploadFile,
    uploadAll,
    cancelUpload,
    cancelAll,
    clearAll,
    retryFailed,
  };
};

export default useFileUpload;