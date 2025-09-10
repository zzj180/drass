import React from 'react';
import {
  Box,
  CircularProgress,
  LinearProgress,
  Typography,
  Skeleton,
} from '@mui/material';

interface LoadingIndicatorProps {
  type?: 'circular' | 'linear' | 'dots' | 'skeleton';
  size?: 'small' | 'medium' | 'large';
  text?: string;
  className?: string;
}

/**
 * Versatile loading indicator component with multiple styles
 */
export const LoadingIndicator: React.FC<LoadingIndicatorProps> = ({
  type = 'dots',
  size = 'medium',
  text,
  className,
}) => {
  const sizeMap = {
    small: 20,
    medium: 30,
    large: 40,
  };

  // Dots animation loading indicator
  const DotsIndicator = () => (
    <Box
      sx={{
        display: 'flex',
        gap: 0.5,
        alignItems: 'center',
      }}
    >
      {[0, 1, 2].map((index) => (
        <Box
          key={index}
          sx={{
            width: size === 'small' ? 6 : size === 'medium' ? 8 : 10,
            height: size === 'small' ? 6 : size === 'medium' ? 8 : 10,
            borderRadius: '50%',
            bgcolor: 'primary.main',
            animation: 'pulse 1.4s infinite ease-in-out',
            animationDelay: `${index * 0.16}s`,
            '@keyframes pulse': {
              '0%, 60%, 100%': {
                transform: 'scale(0.8)',
                opacity: 0.5,
              },
              '30%': {
                transform: 'scale(1)',
                opacity: 1,
              },
            },
          }}
        />
      ))}
    </Box>
  );

  const renderIndicator = () => {
    switch (type) {
      case 'circular':
        return (
          <CircularProgress
            size={sizeMap[size]}
            thickness={size === 'small' ? 4 : 3}
          />
        );
      
      case 'linear':
        return (
          <Box sx={{ width: '100%', maxWidth: 200 }}>
            <LinearProgress />
          </Box>
        );
      
      case 'skeleton':
        return (
          <Box sx={{ width: '100%' }}>
            <Skeleton animation="wave" height={size === 'small' ? 30 : 40} />
            <Skeleton animation="wave" height={size === 'small' ? 30 : 40} width="80%" />
            <Skeleton animation="wave" height={size === 'small' ? 30 : 40} width="60%" />
          </Box>
        );
      
      case 'dots':
      default:
        return <DotsIndicator />;
    }
  };

  return (
    <Box
      className={className}
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 1,
        p: 2,
      }}
    >
      {renderIndicator()}
      
      {text && (
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{
            fontSize: size === 'small' ? '0.75rem' : '0.875rem',
            mt: 1,
          }}
        >
          {text}
        </Typography>
      )}
    </Box>
  );
};

export default LoadingIndicator;