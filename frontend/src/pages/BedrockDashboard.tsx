import React from 'react';
import {
  Box,
  Grid,
  Typography,
  Paper,
  useTheme,
} from '@mui/material';
import {
  Security as SecurityIcon,
  Assessment as AssessmentIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  TrendingUp as TrendingUpIcon,
  Storage as StorageIcon,
} from '@mui/icons-material';

import { DataCard } from '../components/BedrockUI/DataCard/DataCard';
import { StatusBadge } from '../components/BedrockUI/StatusBadge/StatusBadge';
import { GradientButton } from '../components/BedrockUI/GradientButton/GradientButton';

/**
 * 磐石数据合规分析系统 - 仪表盘页面
 * 展示系统核心指标和状态信息
 */
const BedrockDashboard: React.FC = () => {
  const theme = useTheme();

  // 模拟数据
  const dashboardData = {
    complianceScore: 87,
    totalDocuments: 1234,
    riskItems: 23,
    pendingReviews: 8,
    monthlyTrend: '+12%',
    systemStatus: 'online',
  };

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
          磐石数据合规分析系统
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          实时监控数据合规状态，智能识别风险点，确保数据安全合规
        </Typography>
      </Box>

      {/* 核心指标卡片 */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <DataCard
            title="合规评分"
            value={`${dashboardData.complianceScore}%`}
            subtitle="本月平均合规率"
            status="compliant"
            trend="up"
            trendValue={dashboardData.monthlyTrend}
            progress={dashboardData.complianceScore}
            icon={<CheckCircleIcon />}
            onClick={() => console.log('查看合规详情')}
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <DataCard
            title="文档总数"
            value={dashboardData.totalDocuments.toLocaleString()}
            subtitle="已纳入合规管理"
            status="analyzing"
            icon={<StorageIcon />}
            onClick={() => console.log('查看文档列表')}
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <DataCard
            title="风险项目"
            value={dashboardData.riskItems}
            subtitle="需要立即处理"
            status="risk"
            trend="down"
            trendValue="-5"
            icon={<WarningIcon />}
            onClick={() => console.log('查看风险详情')}
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <DataCard
            title="待审核"
            value={dashboardData.pendingReviews}
            subtitle="等待人工审核"
            status="pending"
            icon={<AssessmentIcon />}
            onClick={() => console.log('查看待审核项目')}
          />
        </Grid>
      </Grid>

      {/* 状态展示区域 */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={8}>
          <Paper
            sx={{
              p: 3,
              borderRadius: 2,
              background: 'linear-gradient(145deg, #FFFFFF 0%, #F8FAFC 100%)',
              boxShadow: '0 4px 20px rgba(0, 82, 204, 0.1)',
            }}
          >
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
              合规状态分布
            </Typography>
            
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 3 }}>
              <StatusBadge status="compliant" showIcon pulse />
              <StatusBadge status="warning" showIcon />
              <StatusBadge status="risk" showIcon glow />
              <StatusBadge status="analyzing" showIcon />
              <StatusBadge status="pending" showIcon />
            </Box>

            <Typography variant="body2" color="text.secondary">
              系统正在实时监控 {dashboardData.totalDocuments} 个文档的合规状态，
              当前合规率为 {dashboardData.complianceScore}%，较上月提升 {dashboardData.monthlyTrend}。
            </Typography>
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper
            sx={{
              p: 3,
              borderRadius: 2,
              background: 'linear-gradient(145deg, #FFFFFF 0%, #F8FAFC 100%)',
              boxShadow: '0 4px 20px rgba(0, 82, 204, 0.1)',
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
            }}
          >
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
              系统状态
            </Typography>
            
            <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <StatusBadge status="compliant" label="系统在线" size="small" />
              </Box>
              
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <StatusBadge status="analyzing" label="AI分析中" size="small" pulse />
              </Box>
              
              <Typography variant="caption" color="text.secondary" sx={{ mt: 'auto' }}>
                最后更新: {new Date().toLocaleString()}
              </Typography>
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* 操作按钮区域 */}
      <Paper
        sx={{
          p: 3,
          borderRadius: 2,
          background: 'linear-gradient(145deg, #FFFFFF 0%, #F8FAFC 100%)',
          boxShadow: '0 4px 20px rgba(0, 82, 204, 0.1)',
        }}
      >
        <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
          快速操作
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <GradientButton
            variant="primary"
            startIcon={<SecurityIcon />}
            onClick={() => console.log('开始合规检查')}
            glow
          >
            开始合规检查
          </GradientButton>
          
          <GradientButton
            variant="success"
            startIcon={<AssessmentIcon />}
            onClick={() => console.log('生成报告')}
          >
            生成合规报告
          </GradientButton>
          
          <GradientButton
            variant="info"
            startIcon={<TrendingUpIcon />}
            onClick={() => console.log('查看分析')}
          >
            查看趋势分析
          </GradientButton>
          
          <GradientButton
            variant="warning"
            startIcon={<WarningIcon />}
            onClick={() => console.log('处理风险')}
          >
            处理风险项目
          </GradientButton>
        </Box>
      </Paper>
    </Box>
  );
};

export default BedrockDashboard;
