/**
 * File validation utilities for document upload
 */

export interface FileValidationResult {
  valid: boolean;
  error?: string;
  warnings?: string[];
}

export interface FileTypeConfig {
  extensions: string[];
  mimeTypes: string[];
  maxSize: number;
  icon: string;
}

// Supported file types configuration
export const FILE_TYPES: Record<string, FileTypeConfig> = {
  pdf: {
    extensions: ['.pdf'],
    mimeTypes: ['application/pdf'],
    maxSize: 10 * 1024 * 1024, // 10MB
    icon: '📄',
  },
  word: {
    extensions: ['.doc', '.docx'],
    mimeTypes: [
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    ],
    maxSize: 10 * 1024 * 1024,
    icon: '📝',
  },
  excel: {
    extensions: ['.xls', '.xlsx'],
    mimeTypes: [
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    ],
    maxSize: 10 * 1024 * 1024,
    icon: '📊',
  },
  powerpoint: {
    extensions: ['.ppt', '.pptx'],
    mimeTypes: [
      'application/vnd.ms-powerpoint',
      'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    ],
    maxSize: 10 * 1024 * 1024,
    icon: '📈',
  },
  text: {
    extensions: ['.txt', '.md', '.markdown'],
    mimeTypes: ['text/plain', 'text/markdown'],
    maxSize: 5 * 1024 * 1024, // 5MB for text files
    icon: '📃',
  },
  csv: {
    extensions: ['.csv'],
    mimeTypes: ['text/csv', 'application/csv'],
    maxSize: 5 * 1024 * 1024,
    icon: '📋',
  },
};

// Get all supported extensions
export const SUPPORTED_EXTENSIONS = Object.values(FILE_TYPES)
  .flatMap(type => type.extensions);

// Get all supported MIME types
export const SUPPORTED_MIME_TYPES = Object.values(FILE_TYPES)
  .flatMap(type => type.mimeTypes);

// Default max file size (10MB)
export const DEFAULT_MAX_FILE_SIZE = 10 * 1024 * 1024;

/**
 * Validate a single file
 */
export function validateFile(
  file: File,
  options: {
    maxSize?: number;
    allowedTypes?: string[];
  } = {}
): FileValidationResult {
  const { 
    maxSize = DEFAULT_MAX_FILE_SIZE,
    allowedTypes = SUPPORTED_EXTENSIONS,
  } = options;

  const warnings: string[] = [];

  // Check file extension
  const fileName = file.name.toLowerCase();
  const fileExtension = fileName.substring(fileName.lastIndexOf('.'));
  
  if (!allowedTypes.some(ext => fileName.endsWith(ext.toLowerCase()))) {
    return {
      valid: false,
      error: `File type ${fileExtension} is not supported. Supported types: ${allowedTypes.join(', ')}`,
    };
  }

  // Check file size
  if (file.size > maxSize) {
    return {
      valid: false,
      error: `File size ${formatFileSize(file.size)} exceeds maximum allowed size of ${formatFileSize(maxSize)}`,
    };
  }

  // Check if file is empty
  if (file.size === 0) {
    return {
      valid: false,
      error: 'File is empty',
    };
  }

  // Add warnings for large files
  if (file.size > maxSize * 0.8) {
    warnings.push(`File is large (${formatFileSize(file.size)}). Upload may take longer.`);
  }

  // Check for suspicious file names
  if (fileName.includes('..') || fileName.includes('/') || fileName.includes('\\')) {
    return {
      valid: false,
      error: 'File name contains invalid characters',
    };
  }

  // Check file name length
  if (file.name.length > 255) {
    return {
      valid: false,
      error: 'File name is too long (max 255 characters)',
    };
  }

  return {
    valid: true,
    warnings: warnings.length > 0 ? warnings : undefined,
  };
}

/**
 * Validate multiple files
 */
export function validateFiles(
  files: File[],
  options: {
    maxSize?: number;
    maxFiles?: number;
    maxTotalSize?: number;
    allowedTypes?: string[];
  } = {}
): {
  valid: File[];
  invalid: Array<{ file: File; error: string }>;
  warnings: string[];
} {
  const {
    maxFiles = 10,
    maxTotalSize = 50 * 1024 * 1024, // 50MB total
    ...fileOptions
  } = options;

  const valid: File[] = [];
  const invalid: Array<{ file: File; error: string }> = [];
  const warnings: string[] = [];

  // Check total number of files
  if (files.length > maxFiles) {
    warnings.push(`Only first ${maxFiles} files will be processed. ${files.length - maxFiles} files ignored.`);
    files = files.slice(0, maxFiles);
  }

  // Check total size
  const totalSize = files.reduce((sum, file) => sum + file.size, 0);
  if (totalSize > maxTotalSize) {
    invalid.push(...files.map(file => ({
      file,
      error: `Total size ${formatFileSize(totalSize)} exceeds maximum ${formatFileSize(maxTotalSize)}`,
    })));
    return { valid: [], invalid, warnings };
  }

  // Validate each file
  for (const file of files) {
    const result = validateFile(file, fileOptions);
    if (result.valid) {
      valid.push(file);
      if (result.warnings) {
        warnings.push(...result.warnings);
      }
    } else {
      invalid.push({ file, error: result.error! });
    }
  }

  // Check for duplicate files
  const fileNames = valid.map(f => f.name);
  const duplicates = fileNames.filter((name, index) => fileNames.indexOf(name) !== index);
  if (duplicates.length > 0) {
    warnings.push(`Duplicate files detected: ${duplicates.join(', ')}`);
  }

  return { valid, invalid, warnings };
}

/**
 * Format file size for display
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

/**
 * Get file type from extension
 */
export function getFileType(fileName: string): string {
  const extension = fileName.toLowerCase().substring(fileName.lastIndexOf('.'));
  
  for (const [type, config] of Object.entries(FILE_TYPES)) {
    if (config.extensions.includes(extension)) {
      return type;
    }
  }
  
  return 'unknown';
}

/**
 * Get file icon based on type
 */
export function getFileIcon(fileName: string): string {
  const type = getFileType(fileName);
  return FILE_TYPES[type]?.icon || '📎';
}

/**
 * Check if file type is supported
 */
export function isFileTypeSupported(fileName: string): boolean {
  const extension = fileName.toLowerCase().substring(fileName.lastIndexOf('.'));
  return SUPPORTED_EXTENSIONS.includes(extension);
}

/**
 * Get accept string for file input
 */
export function getAcceptString(): string {
  return SUPPORTED_EXTENSIONS.join(',');
}