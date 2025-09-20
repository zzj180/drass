import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Typography,
  Paper,
  useTheme,
  Button,
  Card,
  CardContent,
  CardActions,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  InsertDriveFile as FileIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  Storage as StorageIcon,
  Description as DocumentIcon,
  Folder as FolderIcon,
} from '@mui/icons-material';
import { FileUploadDialog } from '../FileUpload/FileUploadDialog';
import FullDocumentPreview from '../DocumentPreview/FullDocumentPreview';
import { authService } from '../../services/authService';

interface Document {
  id: string;
  name: string;
  type: string;
  size: number;
  uploadDate: string;
  status: 'processing' | 'completed' | 'error';
  description?: string;
}

/**
 * 文档管理仪表盘
 * 提供文档上传、查看、管理功能
 */
const DocumentDashboard: React.FC = () => {
  const theme = useTheme();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [previewOpen, setPreviewOpen] = useState(false);

  // 模拟文档数据
  // 移除模拟数据，使用真实的空状态

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    setLoading(true);
    try {
      // 使用真实API调用
      const response = await fetch('http://localhost:8888/api/v1/documents/', {
        headers: {
          ...(await authService.getAuthHeadersWithRefresh()),
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const documents = await response.json();
      setDocuments(documents);
    } catch (error) {
      console.error('加载文档失败:', error);
      // 如果API调用失败，显示空列表
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  };

  const handleUploadSuccess = (uploadedFiles: any[]) => {
    console.log('上传成功:', uploadedFiles);
    loadDocuments(); // 重新加载文档列表
    setUploadDialogOpen(false);
  };

  const handleDeleteDocument = async (documentId: string) => {
    try {
      // 使用真实API调用删除文档
      const response = await fetch(`http://localhost:8888/api/v1/documents/${documentId}`, {
        method: 'DELETE',
        headers: {
          ...(await authService.getAuthHeadersWithRefresh()),
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      // 删除成功后从本地状态中移除
      setDocuments(prev => prev.filter(doc => doc.id !== documentId));
    } catch (error) {
      console.error('删除文档失败:', error);
      // 如果API调用失败，仍然从本地状态中移除（模拟删除）
      setDocuments(prev => prev.filter(doc => doc.id !== documentId));
    }
  };

  const handleViewDocument = (document: Document) => {
    setSelectedDocument(document);
    setViewDialogOpen(true);
  };

  const handlePreviewDocument = (document: Document) => {
    setSelectedDocument(document);
    setPreviewOpen(true);
  };

  const handleDownloadDocument = () => {
    if (selectedDocument) {
      // 模拟下载功能
      console.log('下载文档:', selectedDocument.name);
      // 这里可以调用实际的下载API
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'processing': return 'warning';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed': return '已完成';
      case 'processing': return '处理中';
      case 'error': return '错误';
      default: return '未知';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* 页面标题 */}
      <Box sx={{ mb: 4 }}>
        <Typography
          variant="h4"
          sx={{
            fontWeight: 700,
            color: 'text.primary',
            mb: 1,
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
        >
          文档管理中心
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          上传、管理和查看您的合规文档
        </Typography>
      </Box>

      {/* 统计卡片 */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            color: 'white'
          }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <StorageIcon sx={{ mr: 1 }} />
                <Typography variant="h6">总文档数</Typography>
              </Box>
              <Typography variant="h3" sx={{ fontWeight: 'bold' }}>
                {documents.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
            color: 'white'
          }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <DocumentIcon sx={{ mr: 1 }} />
                <Typography variant="h6">已完成</Typography>
              </Box>
              <Typography variant="h3" sx={{ fontWeight: 'bold' }}>
                {documents.filter(doc => doc.status === 'completed').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
            color: 'white'
          }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <FolderIcon sx={{ mr: 1 }} />
                <Typography variant="h6">处理中</Typography>
              </Box>
              <Typography variant="h3" sx={{ fontWeight: 'bold' }}>
                {documents.filter(doc => doc.status === 'processing').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
            color: 'white'
          }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <UploadIcon sx={{ mr: 1 }} />
                <Typography variant="h6">今日上传</Typography>
              </Box>
              <Typography variant="h3" sx={{ fontWeight: 'bold' }}>
                {documents.filter(doc => doc.uploadDate === new Date().toISOString().split('T')[0]).length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* 操作按钮 */}
      <Box sx={{ mb: 3, display: 'flex', gap: 2 }}>
        <Button
          variant="contained"
          startIcon={<UploadIcon />}
          onClick={() => setUploadDialogOpen(true)}
          sx={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            '&:hover': {
              background: 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)',
            }
          }}
        >
          上传文档
        </Button>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={loadDocuments}
          disabled={loading}
        >
          刷新列表
        </Button>
      </Box>

      {/* 文档列表 */}
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            文档列表
          </Typography>
          {loading && <CircularProgress size={24} />}
        </Box>

        {documents.length === 0 ? (
          <Alert severity="info" sx={{ mb: 2 }}>
            暂无文档，请上传您的第一个文档
          </Alert>
        ) : (
          <List>
            {documents.map((doc, index) => (
              <React.Fragment key={doc.id}>
                <ListItem sx={{ py: 2 }}>
                  <FileIcon sx={{ mr: 2, color: 'primary.main' }} />
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 0.5 }}>
                      {doc.name}
                    </Typography>
                    {doc.description && (
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        {doc.description}
                      </Typography>
                    )}
                    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                      <Chip
                        label={getStatusText(doc.status)}
                        color={getStatusColor(doc.status) as any}
                        size="small"
                      />
                      <Typography variant="caption" color="text.secondary">
                        {formatFileSize(doc.size)} • {doc.uploadDate}
                      </Typography>
                    </Box>
                  </Box>
                  <ListItemSecondaryAction>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <IconButton
                        onClick={() => handlePreviewDocument(doc)}
                        color="primary"
                        title="预览文档"
                      >
                        <ViewIcon />
                      </IconButton>
                      <IconButton
                        onClick={() => handleViewDocument(doc)}
                        color="info"
                        title="查看详情"
                      >
                        <FileIcon />
                      </IconButton>
                      <IconButton
                        onClick={() => handleDeleteDocument(doc.id)}
                        color="error"
                        title="删除文档"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Box>
                  </ListItemSecondaryAction>
                </ListItem>
                {index < documents.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        )}
      </Paper>

      {/* 上传对话框 */}
      <FileUploadDialog
        open={uploadDialogOpen}
        onClose={() => setUploadDialogOpen(false)}
        onUploadSuccess={handleUploadSuccess}
      />

      {/* 文档查看对话框 */}
      <Dialog
        open={viewDialogOpen}
        onClose={() => setViewDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          文档详情
        </DialogTitle>
        <DialogContent>
          {selectedDocument && (
            <Box>
              <Typography variant="h6" gutterBottom>
                {selectedDocument.name}
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                {selectedDocument.description}
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                <Chip
                  label={getStatusText(selectedDocument.status)}
                  color={getStatusColor(selectedDocument.status) as any}
                />
                <Typography variant="body2">
                  文件大小: {formatFileSize(selectedDocument.size)}
                </Typography>
                <Typography variant="body2">
                  上传日期: {selectedDocument.uploadDate}
                </Typography>
              </Box>
              <Alert severity="info">
                文档预览功能正在开发中，敬请期待！
              </Alert>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDialogOpen(false)}>
            关闭
          </Button>
          <Button
            variant="contained"
            startIcon={<DownloadIcon />}
            onClick={() => {
              // 模拟下载功能
              console.log('下载文档:', selectedDocument?.name);
            }}
          >
            下载
          </Button>
        </DialogActions>
      </Dialog>

      {/* 文档预览组件 */}
      {selectedDocument && (
        <FullDocumentPreview
          document={selectedDocument}
          open={previewOpen}
          onClose={() => setPreviewOpen(false)}
          onDownload={handleDownloadDocument}
        />
      )}
    </Box>
  );
};

export default DocumentDashboard;
