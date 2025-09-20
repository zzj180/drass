import React from 'react';
import { Box, Typography, Paper } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { Upload as UploadIcon, History as HistoryIcon, Storage as StorageIcon } from '@mui/icons-material';
import { GradientButton, StatusBadge } from '../BedrockUI';

export const KnowledgeBase: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  return (
    <Box sx={{ width: '100%' }}>
      {/* 页面标题 */}
      <Box sx={{ mb: 4 }}>
        <Typography
          variant="h4"
          sx={{
            fontWeight: 700,
            color: 'text.primary',
            mb: 1,
            background: 'linear-gradient(135deg, #8E44AD 0%, #BB8FCE 100%)',
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
        >
          {t('knowledgeBase.title') || '知识库管理'}
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          {t('knowledgeBase.management') || '管理和维护数据合规知识库'}
        </Typography>
      </Box>

      <Paper
        sx={{
          p: 3,
          borderRadius: 2,
          background: 'linear-gradient(145deg, #FFFFFF 0%, #F8FAFC 100%)',
          boxShadow: '0 4px 20px rgba(142, 68, 173, 0.1)',
        }}
      >
        {/* 状态指示 */}
        <Box sx={{ display: 'flex', gap: 2, mb: 3, alignItems: 'center' }}>
          <StorageIcon sx={{ color: 'secondary.main' }} />
          <StatusBadge status="compliant" label="知识库在线" showIcon />
          <StatusBadge status="analyzing" label="处理中" showIcon pulse />
        </Box>

        {/* 操作按钮区域 */}
        <Box sx={{ display: 'flex', gap: 2, mb: 4, flexWrap: 'wrap' }}>
          <GradientButton
            variant="secondary"
            startIcon={<UploadIcon />}
            glow
            onClick={() => console.log('上传文档')}
          >
            {t('knowledgeBase.upload') || '上传文档'}
          </GradientButton>

          <GradientButton
            variant="info"
            startIcon={<HistoryIcon />}
            onClick={() => navigate('/knowledge-base/access-logs')}
          >
            {t('knowledgeBase.viewAccessLogs') || '查看访问日志'}
          </GradientButton>
        </Box>

        {/* 最近文档区域 */}
        <Box>
          <Typography 
            variant="h6" 
            gutterBottom
            sx={{ fontWeight: 600, color: 'text.primary' }}
          >
            {t('knowledgeBase.recentDocuments') || '最近文档'}
          </Typography>

          <Box
            sx={{
              p: 3,
              border: '2px dashed',
              borderColor: 'grey.300',
              borderRadius: 2,
              textAlign: 'center',
              background: 'rgba(142, 68, 173, 0.02)',
            }}
          >
            <StorageIcon sx={{ fontSize: 48, color: 'grey.400', mb: 1 }} />
            <Typography color="text.secondary">
              {t('table.noData') || '暂无数据'}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              上传您的第一个合规文档开始使用
            </Typography>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};