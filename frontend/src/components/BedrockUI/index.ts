/**
 * 磐石数据合规分析系统 - UI组件库
 * Bedrock Data Compliance Analysis System - UI Component Library
 */

// 数据卡片组件
export { DataCard } from './DataCard/DataCard';
export type { DataCardProps, DataCardStatus, DataCardTrend } from './DataCard/DataCard';

// 状态徽章组件
export { StatusBadge } from './StatusBadge/StatusBadge';
export type { StatusBadgeProps, StatusBadgeVariant, StatusBadgeSize } from './StatusBadge/StatusBadge';

// 渐变按钮组件
export { GradientButton } from './GradientButton/GradientButton';
export type { GradientButtonProps, GradientButtonVariant } from './GradientButton/GradientButton';

// 主题配置
export { bedrockColors, bedrockDarkColors, chartColors } from '../../theme/bedrock/colors';
export { gradients } from '../../theme/bedrock/gradients';
export { animations, durations, easings } from '../../theme/bedrock/animations';
