import React from 'react';
import { Box, Typography, Grid } from '@mui/material';
import { useTranslation } from 'react-i18next';
import {
  Storage as StorageIcon,
  Chat as ChatIcon,
  People as PeopleIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { DataCard, StatusBadge } from '../BedrockUI';

export const Dashboard: React.FC = () => {
  const { t } = useTranslation();

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
            background: 'linear-gradient(135deg, #0052CC 0%, #4A90E2 100%)',
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
        >
          {t('dashboard.title') || '系统概览'}
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          数据合规管理系统运行状态总览
        </Typography>
      </Box>

      {/* 核心指标卡片 */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <DataCard
            title={t('dashboard.totalDocuments') || '文档总数'}
            value="42"
            subtitle="已纳入合规管理"
            status="analyzing"
            icon={<StorageIcon />}
            onClick={() => console.log('查看文档列表')}
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <DataCard
            title={t('dashboard.totalQueries') || '查询次数'}
            value="156"
            subtitle="本月总查询数"
            status="compliant"
            trend="up"
            trendValue="+23%"
            icon={<ChatIcon />}
            onClick={() => console.log('查看查询详情')}
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <DataCard
            title={t('dashboard.activeUsers') || '活跃用户'}
            value="8"
            subtitle="当前在线用户"
            status="pending"
            icon={<PeopleIcon />}
            onClick={() => console.log('查看用户列表')}
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <DataCard
            title={t('dashboard.systemStatus') || '系统状态'}
            value="正常"
            subtitle={t('knowledgeBase.ready') || '系统运行正常'}
            status="compliant"
            icon={<CheckCircleIcon />}
            onClick={() => console.log('查看系统详情')}
          />
        </Grid>
      </Grid>

      {/* 状态展示区域 */}
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <StatusBadge status="compliant" showIcon pulse />
        <StatusBadge status="analyzing" showIcon />
        <StatusBadge status="pending" showIcon />
      </Box>
    </Box>
  );
};