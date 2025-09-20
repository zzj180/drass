import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  CircularProgress,
  Alert,
  IconButton,
  Toolbar,
  AppBar,
  Button,
  Chip,
  Slider,
} from '@mui/material';
import {
  Close as CloseIcon,
  Download as DownloadIcon,
  Fullscreen as FullscreenIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  Refresh as RefreshIcon,
  NavigateBefore as PrevPageIcon,
  NavigateNext as NextPageIcon,
  FirstPage as FirstPageIcon,
  LastPage as LastPageIcon,
} from '@mui/icons-material';

// 动态导入 react-pdf 以避免 SSR 问题
let Document: any = null;
let Page: any = null;
let pdfjs: any = null;

const loadReactPDF = async () => {
  if (!Document) {
    const reactPDF = await import('react-pdf');
    Document = reactPDF.Document;
    Page = reactPDF.Page;
    pdfjs = reactPDF.pdfjs;
    
    // 设置 PDF.js worker
    pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.js`;
  }
  return { Document, Page, pdfjs };
};

interface PDFPreviewProps {
  document: {
    id: string;
    name: string;
    type: string;
    size: number;
    uploadDate: string;
    status: string;
    description?: string;
    url?: string;
  };
  open: boolean;
  onClose: () => void;
  onDownload?: () => void;
}

/**
 * PDF预览组件
 * 支持PDF文件的完整预览功能
 */
const PDFPreview: React.FC<PDFPreviewProps> = ({
  document,
  open,
  onClose,
  onDownload,
}) => {
  const [numPages, setNumPages] = useState<number | null>(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [scale, setScale] = useState(1.0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [reactPDFLoaded, setReactPDFLoaded] = useState(false);

  // 加载 react-pdf
  useEffect(() => {
    if (open) {
      loadReactPDF()
        .then(() => {
          setReactPDFLoaded(true);
        })
        .catch((err) => {
          console.error('Failed to load react-pdf:', err);
          setError('PDF预览库加载失败');
        });
    }
  }, [open]);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleZoomIn = () => {
    setScale(prev => Math.min(prev + 0.2, 3.0));
  };

  const handleZoomOut = () => {
    setScale(prev => Math.max(prev - 0.2, 0.5));
  };

  const handleResetZoom = () => {
    setScale(1.0);
  };

  const handleScaleChange = (event: Event, newValue: number | number[]) => {
    setScale(newValue as number);
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  const goToFirstPage = () => {
    setPageNumber(1);
  };

  const goToLastPage = () => {
    if (numPages) {
      setPageNumber(numPages);
    }
  };

  const goToPrevPage = () => {
    setPageNumber(prev => Math.max(prev - 1, 1));
  };

  const goToNextPage = () => {
    if (numPages) {
      setPageNumber(prev => Math.min(prev + 1, numPages));
    }
  };

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
    setPageNumber(1);
    setError(null);
  };

  const onDocumentLoadError = (error: Error) => {
    setError('PDF加载失败: ' + error.message);
    console.error('PDF load error:', error);
  };

  const onPageLoadSuccess = () => {
    setLoading(false);
  };

  const onPageLoadError = (error: Error) => {
    setError('页面加载失败: ' + error.message);
    setLoading(false);
  };

  if (!open) return null;

  return (
    <Box
      sx={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        zIndex: 9999,
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* 工具栏 */}
      <AppBar position="static" sx={{ backgroundColor: 'rgba(0, 0, 0, 0.9)' }}>
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1, color: 'white' }}>
            {document.name}
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Chip
              label={document.status}
              color={document.status === 'completed' ? 'success' : 'warning'}
              size="small"
              sx={{ color: 'white' }}
            />
            
            {/* 缩放控制 */}
            <IconButton onClick={handleZoomOut} color="inherit" size="small">
              <ZoomOutIcon />
            </IconButton>
            <Typography variant="body2" sx={{ color: 'white', minWidth: '60px', textAlign: 'center' }}>
              {Math.round(scale * 100)}%
            </Typography>
            <IconButton onClick={handleZoomIn} color="inherit" size="small">
              <ZoomInIcon />
            </IconButton>
            <IconButton onClick={handleResetZoom} color="inherit" size="small">
              <RefreshIcon />
            </IconButton>
            
            <IconButton onClick={toggleFullscreen} color="inherit" size="small">
              <FullscreenIcon />
            </IconButton>
            
            {onDownload && (
              <Button
                startIcon={<DownloadIcon />}
                onClick={onDownload}
                variant="outlined"
                size="small"
                sx={{ color: 'white', borderColor: 'white' }}
              >
                下载
              </Button>
            )}
            
            <IconButton onClick={onClose} color="inherit">
              <CloseIcon />
            </IconButton>
          </Box>
        </Toolbar>
      </AppBar>

      {/* 页面导航栏 */}
      {numPages && numPages > 1 && (
        <Box sx={{ 
          backgroundColor: 'rgba(0, 0, 0, 0.7)', 
          color: 'white', 
          p: 1,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          gap: 2
        }}>
          <IconButton onClick={goToFirstPage} color="inherit" size="small" disabled={pageNumber <= 1}>
            <FirstPageIcon />
          </IconButton>
          <IconButton onClick={goToPrevPage} color="inherit" size="small" disabled={pageNumber <= 1}>
            <PrevPageIcon />
          </IconButton>
          <Typography variant="body2">
            {pageNumber} / {numPages}
          </Typography>
          <IconButton onClick={goToNextPage} color="inherit" size="small" disabled={pageNumber >= numPages}>
            <NextPageIcon />
          </IconButton>
          <IconButton onClick={goToLastPage} color="inherit" size="small" disabled={pageNumber >= numPages}>
            <LastPageIcon />
          </IconButton>
        </Box>
      )}

      {/* 缩放滑块 */}
      <Box sx={{ 
        backgroundColor: 'rgba(0, 0, 0, 0.7)', 
        color: 'white', 
        p: 1,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        gap: 2
      }}>
        <Typography variant="body2" sx={{ color: 'white' }}>
          缩放:
        </Typography>
        <Box sx={{ width: 200 }}>
          <Slider
            value={scale}
            onChange={handleScaleChange}
            min={0.5}
            max={3.0}
            step={0.1}
            valueLabelDisplay="auto"
            valueLabelFormat={(value) => `${Math.round(value * 100)}%`}
            sx={{
              color: 'white',
              '& .MuiSlider-thumb': {
                backgroundColor: 'white',
              },
              '& .MuiSlider-track': {
                backgroundColor: 'white',
              },
              '& .MuiSlider-rail': {
                backgroundColor: 'rgba(255, 255, 255, 0.3)',
              },
            }}
          />
        </Box>
      </Box>

      {/* 预览内容区域 */}
      <Box
        sx={{
          flex: 1,
          overflow: 'auto',
          backgroundColor: '#f5f5f5',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'flex-start',
          p: 2,
        }}
      >
        {!reactPDFLoaded && (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mt: 4 }}>
            <CircularProgress size={60} />
            <Typography variant="body1" sx={{ mt: 2 }}>
              正在加载PDF预览库...
            </Typography>
          </Box>
        )}

        {reactPDFLoaded && (
          <Paper
            elevation={3}
            sx={{
              maxWidth: isFullscreen ? '100%' : '90%',
              maxHeight: isFullscreen ? '100%' : '90%',
              overflow: 'auto',
              backgroundColor: 'white',
              p: 2,
            }}
          >
            {Document && Page ? (
              <Document
                file={document.url || '/api/documents/' + document.id}
                onLoadSuccess={onDocumentLoadSuccess}
                onLoadError={onDocumentLoadError}
                loading={
                  <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                    <CircularProgress />
                    <Typography variant="body2" sx={{ ml: 2 }}>
                      正在加载PDF文档...
                    </Typography>
                  </Box>
                }
                error={
                  <Alert severity="error" sx={{ m: 2 }}>
                    PDF文档加载失败
                  </Alert>
                }
              >
                <Page
                  pageNumber={pageNumber}
                  scale={scale}
                  onLoadSuccess={onPageLoadSuccess}
                  onLoadError={onPageLoadError}
                  renderTextLayer={true}
                  renderAnnotationLayer={true}
                  loading={
                    <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                      <CircularProgress />
                    </Box>
                  }
                />
              </Document>
            ) : (
              <Alert severity="error" sx={{ m: 2 }}>
                PDF预览组件加载失败
              </Alert>
            )}
          </Paper>
        )}

        {error && (
          <Alert severity="error" sx={{ mt: 4, maxWidth: 600 }}>
            {error}
          </Alert>
        )}
      </Box>
    </Box>
  );
};

export default PDFPreview;
