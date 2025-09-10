import React from 'react';
import { Typography, Box, LinearProgress } from '@mui/material';

interface CharacterCounterProps {
  current: number;
  max: number;
  showProgress?: boolean;
  className?: string;
}

/**
 * Character counter component displays character count and optional progress bar
 */
export const CharacterCounter: React.FC<CharacterCounterProps> = ({
  current,
  max,
  showProgress = true,
  className,
}) => {
  const percentage = (current / max) * 100;
  const isNearLimit = percentage > 80;
  const isAtLimit = percentage >= 100;
  
  const getColor = () => {
    if (isAtLimit) return 'error';
    if (isNearLimit) return 'warning';
    return 'text.secondary';
  };
  
  return (
    <Box className={className} sx={{ minWidth: 100 }}>
      {showProgress && percentage > 50 && (
        <LinearProgress
          variant="determinate"
          value={Math.min(percentage, 100)}
          color={isAtLimit ? 'error' : isNearLimit ? 'warning' : 'primary'}
          sx={{
            height: 2,
            mb: 0.5,
            bgcolor: 'action.hover',
          }}
        />
      )}
      
      <Typography
        variant="caption"
        color={getColor()}
        sx={{
          display: 'block',
          textAlign: 'right',
          fontSize: '0.75rem',
        }}
      >
        {current.toLocaleString()} / {max.toLocaleString()}
      </Typography>
    </Box>
  );
};