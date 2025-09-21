import React, { useState } from 'react';
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Divider,
  useTheme,
  useMediaQuery,
  styled,
  Avatar,
  Chip,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Chat as ChatIcon,
  ChevronLeft as ChevronLeftIcon,
  Security as SecurityIcon,
  Dashboard as DashboardIcon,
  Assignment as AuditIcon,
  Assessment as AssessmentIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { gradients } from '../theme/bedrock/gradients';
import { bedrockColors } from '../theme/bedrock/colors';

const drawerWidth = 280;

interface MainLayoutProps {
  children: React.ReactNode;
}

// 样式化组件
const StyledAppBar = styled(AppBar)(({ theme }) => ({
  background: gradients.primary.main,
  backdropFilter: 'blur(10px)',
  boxShadow: '0 8px 32px rgba(0, 82, 204, 0.3)',
  borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
  zIndex: theme.zIndex.drawer + 1,
}));

const StyledDrawer = styled(Drawer)(({ theme }) => ({
  '& .MuiDrawer-paper': {
    width: drawerWidth,
    background: 'linear-gradient(180deg, #1A202C 0%, #2D3748 100%)',
    borderRight: `1px solid ${bedrockColors.border.dark}`,
    color: bedrockColors.text.inverse,
  },
}));

const LogoContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  padding: theme.spacing(2),
  background: gradients.primary.dark,
  position: 'relative',
  overflow: 'hidden',
  
  '&::before': {
    content: '""',
    position: 'absolute',
    top: 0,
    left: '-100%',
    width: '100%',
    height: '100%',
    background: 'linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent)',
    animation: 'logoShimmer 3s infinite',
  },
  
  '@keyframes logoShimmer': {
    '0%': { left: '-100%' },
    '100%': { left: '100%' },
  },
}));

const MenuItemButton = styled(ListItemButton, {
  shouldForwardProp: (prop) => prop !== 'selected' && prop !== 'menuColor',
})<{ selected?: boolean; menuColor?: string }>(({ theme, selected, menuColor }) => ({
  margin: '4px 12px',
  borderRadius: '12px',
  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
  position: 'relative',
  overflow: 'hidden',
  
  ...(selected && {
    background: menuColor || gradients.primary.main,
    color: 'white',
    '&::before': {
      content: '""',
      position: 'absolute',
      left: 0,
      top: 0,
      bottom: 0,
      width: 4,
      background: 'white',
      borderRadius: '0 4px 4px 0',
    },
  }),
  
  '&:hover': {
    background: selected 
      ? menuColor || gradients.primary.main
      : 'rgba(255, 255, 255, 0.08)',
    transform: 'translateX(4px)',
  },
  
  '& .MuiListItemIcon-root': {
    color: selected ? 'white' : bedrockColors.text.secondary,
    minWidth: 40,
  },
  
  '& .MuiListItemText-root': {
    '& .MuiTypography-root': {
      fontWeight: selected ? 600 : 400,
      fontSize: '0.875rem',
    },
  },
}));

const StatusIndicator = styled(Box)(({ theme }) => ({
  position: 'absolute',
  top: 8,
  right: 8,
  width: 8,
  height: 8,
  borderRadius: '50%',
  background: gradients.success.main,
  animation: 'pulse 2s infinite',
  
  '@keyframes pulse': {
    '0%, 100%': {
      opacity: 1,
      transform: 'scale(1)',
    },
    '50%': {
      opacity: 0.7,
      transform: 'scale(1.2)',
    },
  },
}));

/**
 * Main application layout with sidebar navigation
 */
const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const { t } = useTranslation();

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const menuItems = [
    { 
      text: '知识库', 
      icon: <DashboardIcon />, 
      path: '/dashboard',
      color: gradients.primary.main,
    },
    { 
      text: '数据合规分析助手', 
      icon: <ChatIcon />, 
      path: '/chat',
      color: gradients.primary.main,
    },
    { 
      text: '审计日志', 
      icon: <AuditIcon />, 
      path: '/audit-logs',
      color: gradients.primary.main,
    },
  ];

  const drawer = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <LogoContainer>
        <Avatar
          sx={{
            width: 40,
            height: 40,
            background: gradients.primary.main,
            mr: 2,
          }}
        >
          <SecurityIcon />
        </Avatar>
        <Box>
          <Typography 
            variant="h6" 
            sx={{ 
              color: 'white', 
              fontWeight: 700,
              fontSize: '1.1rem',
              lineHeight: 1.2,
            }}
          >
            磐石数据合规
          </Typography>
          <Typography 
            variant="caption" 
            sx={{ 
              color: 'rgba(255, 255, 255, 0.7)',
              fontSize: '0.75rem',
            }}
          >
            分析系统
          </Typography>
        </Box>
        <StatusIndicator />
        {isMobile && (
          <IconButton 
            onClick={handleDrawerToggle} 
            sx={{ ml: 'auto', color: 'white' }}
          >
            <ChevronLeftIcon />
          </IconButton>
        )}
      </LogoContainer>

      <Box sx={{ p: 2 }}>
        <Chip
          label="在线"
          size="small"
          sx={{
            background: gradients.success.main,
            color: 'white',
            fontSize: '0.7rem',
            height: 20,
          }}
        />
      </Box>

      <Divider sx={{ borderColor: 'rgba(255, 255, 255, 0.1)' }} />
      
      <List sx={{ flex: 1, pt: 2 }}>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <MenuItemButton
              selected={location.pathname === item.path}
              menuColor={item.color}
              onClick={() => {
                navigate(item.path);
                if (isMobile) {
                  setMobileOpen(false);
                }
              }}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </MenuItemButton>
          </ListItem>
        ))}
      </List>

      <Divider sx={{ borderColor: 'rgba(255, 255, 255, 0.1)' }} />
      
      <Box sx={{ p: 2 }}>
        <Typography 
          variant="caption" 
          sx={{ 
            color: 'rgba(255, 255, 255, 0.5)',
            fontSize: '0.7rem',
          }}
        >
          © 2025 磐石科技
        </Typography>
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      {isMobile && (
        <StyledAppBar position="fixed">
          <Toolbar>
            <IconButton
              color="inherit"
              aria-label="open drawer"
              edge="start"
              onClick={handleDrawerToggle}
              sx={{ mr: 2, display: { sm: 'none' } }}
            >
              <MenuIcon />
            </IconButton>
            <Typography 
              variant="h6" 
              noWrap 
              component="div"
              sx={{ fontWeight: 600 }}
            >
              磐石数据合规分析系统
            </Typography>
          </Toolbar>
        </StyledAppBar>
      )}

      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
      >
        <StyledDrawer
          variant={isMobile ? 'temporary' : 'permanent'}
          open={isMobile ? mobileOpen : true}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better open performance on mobile
          }}
        >
          {drawer}
        </StyledDrawer>
      </Box>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          background: `linear-gradient(135deg, ${bedrockColors.background.default} 0%, ${bedrockColors.background.surface} 100%)`,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          mt: isMobile ? 8 : 0,
          position: 'relative',
          overflow: 'auto',
          
          // 添加科技感背景纹理
          '&::before': {
            content: '""',
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundImage: `
              radial-gradient(circle at 20% 20%, rgba(74, 144, 226, 0.05) 0%, transparent 50%),
              radial-gradient(circle at 80% 80%, rgba(142, 68, 173, 0.05) 0%, transparent 50%),
              radial-gradient(circle at 40% 60%, rgba(0, 179, 134, 0.05) 0%, transparent 50%)
            `,
            pointerEvents: 'none',
            zIndex: 0,
          },
        }}
      >
        <Box sx={{ position: 'relative', zIndex: 1, p: 3 }}>
          {children}
        </Box>
      </Box>
    </Box>
  );
};

export default MainLayout;