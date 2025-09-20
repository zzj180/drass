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
} from '@mui/material';
import {
  Close as CloseIcon,
  Download as DownloadIcon,
  Fullscreen as FullscreenIcon,
} from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';

interface DocumentPreviewProps {
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
 * 简化版文档预览组件
 * 目前只支持Markdown格式的预览
 */
const SimpleDocumentPreview: React.FC<DocumentPreviewProps> = ({
  document,
  open,
  onClose,
  onDownload,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [markdownContent, setMarkdownContent] = useState<string>('');
  const [isFullscreen, setIsFullscreen] = useState(false);

  // 根据文件扩展名确定文件类型
  const getFileType = (filename: string): string => {
    const extension = filename.split('.').pop()?.toLowerCase();
    return extension || '';
  };

  const fileType = getFileType(document.name);

  // 模拟获取文档内容
  const loadDocumentContent = async () => {
    setLoading(true);
    setError(null);
    
    try {
      if (fileType === 'md' || fileType === 'markdown') {
        // 模拟Markdown内容
        const mockMarkdown = `# ${document.name}

## 文档描述
${document.description || '暂无描述'}

## 基本信息
- **文件名**: ${document.name}
- **文件大小**: ${formatFileSize(document.size)}
- **上传日期**: ${document.uploadDate}
- **状态**: ${document.status}

## 内容预览

这是一个**Markdown文档**的预览示例。

### 功能特性
- ✅ 支持标题
- ✅ 支持列表
- ✅ 支持代码块
- ✅ 支持表格

### 代码示例
\`\`\`javascript
function hello() {
  console.log("Hello, World!");
}
\`\`\`

### 表格示例
| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 数据1 | 数据2 | 数据3 |
| 数据4 | 数据5 | 数据6 |

> 这是一个引用块

---

*文档预览功能正在开发中，更多功能敬请期待！*`;

        setMarkdownContent(mockMarkdown);
      } else if (fileType === 'pdf') {
        setError('PDF预览功能正在开发中，敬请期待！');
      } else {
        setError('不支持的文件格式');
      }
    } catch (err) {
      setError('加载文档内容失败');
      console.error('加载文档失败:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (open && document) {
      loadDocumentContent();
    }
  }, [open, document]);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
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
        {loading && (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mt: 4 }}>
            <CircularProgress size={60} />
            <Typography variant="body1" sx={{ mt: 2 }}>
              正在加载文档...
            </Typography>
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ mt: 4, maxWidth: 600 }}>
            {error}
          </Alert>
        )}

        {!loading && !error && (
          <Paper
            elevation={3}
            sx={{
              maxWidth: isFullscreen ? '100%' : '90%',
              maxHeight: isFullscreen ? '100%' : '90%',
              overflow: 'auto',
              backgroundColor: 'white',
            }}
          >
            {fileType === 'md' || fileType === 'markdown' ? (
              <Box sx={{ p: 3 }}>
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  rehypePlugins={[rehypeHighlight]}
                  components={{
                    // 自定义样式
                    h1: ({ children }) => (
                      <Typography variant="h4" sx={{ mb: 2, mt: 3, fontWeight: 'bold' }}>
                        {children}
                      </Typography>
                    ),
                    h2: ({ children }) => (
                      <Typography variant="h5" sx={{ mb: 2, mt: 2, fontWeight: 'bold' }}>
                        {children}
                      </Typography>
                    ),
                    h3: ({ children }) => (
                      <Typography variant="h6" sx={{ mb: 1, mt: 2, fontWeight: 'bold' }}>
                        {children}
                      </Typography>
                    ),
                    p: ({ children }) => (
                      <Typography variant="body1" sx={{ mb: 2, lineHeight: 1.6 }}>
                        {children}
                      </Typography>
                    ),
                    code: ({ children, className }) => {
                      const isInline = !className;
                      return isInline ? (
                        <code style={{ 
                          backgroundColor: '#f5f5f5', 
                          padding: '2px 4px', 
                          borderRadius: '3px',
                          fontFamily: 'monospace'
                        }}>
                          {children}
                        </code>
                      ) : (
                        <code className={className}>{children}</code>
                      );
                    },
                    pre: ({ children }) => (
                      <Box
                        component="pre"
                        sx={{
                          backgroundColor: '#f8f8f8',
                          border: '1px solid #e1e1e1',
                          borderRadius: '4px',
                          padding: '16px',
                          overflow: 'auto',
                          mb: 2,
                        }}
                      >
                        {children}
                      </Box>
                    ),
                    blockquote: ({ children }) => (
                      <Box
                        sx={{
                          borderLeft: '4px solid #ddd',
                          paddingLeft: '16px',
                          marginLeft: 0,
                          marginRight: 0,
                          marginY: 2,
                          fontStyle: 'italic',
                          color: '#666',
                        }}
                      >
                        {children}
                      </Box>
                    ),
                    table: ({ children }) => (
                      <Box sx={{ overflow: 'auto', mb: 2 }}>
                        <table style={{ 
                          width: '100%', 
                          borderCollapse: 'collapse',
                          border: '1px solid #ddd'
                        }}>
                          {children}
                        </table>
                      </Box>
                    ),
                    th: ({ children }) => (
                      <th style={{ 
                        border: '1px solid #ddd', 
                        padding: '8px', 
                        backgroundColor: '#f5f5f5',
                        fontWeight: 'bold'
                      }}>
                        {children}
                      </th>
                    ),
                    td: ({ children }) => (
                      <td style={{ 
                        border: '1px solid #ddd', 
                        padding: '8px' 
                      }}>
                        {children}
                      </td>
                    ),
                  }}
                >
                  {markdownContent}
                </ReactMarkdown>
              </Box>
            ) : (
              <Alert severity="warning" sx={{ m: 2 }}>
                不支持预览此文件格式: {fileType}
              </Alert>
            )}
          </Paper>
        )}
      </Box>
    </Box>
  );
};

export default SimpleDocumentPreview;
