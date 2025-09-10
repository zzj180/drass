import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface Toast {
  id: string;
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

interface Modal {
  id: string;
  type: 'confirm' | 'alert' | 'custom';
  title?: string;
  message?: string;
  component?: React.ComponentType;
  props?: Record<string, any>;
  onConfirm?: () => void;
  onCancel?: () => void;
}

interface Drawer {
  open: boolean;
  anchor: 'left' | 'right' | 'top' | 'bottom';
  component?: React.ComponentType;
  props?: Record<string, any>;
}

interface UIState {
  sidebarOpen: boolean;
  sidebarCollapsed: boolean;
  rightPanelOpen: boolean;
  fullscreen: boolean;
  loading: {
    global: boolean;
    tasks: Record<string, boolean>;
  };
  toasts: Toast[];
  modals: Modal[];
  drawer: Drawer;
  breadcrumbs: Array<{
    label: string;
    path?: string;
  }>;
  activeView: 'chat' | 'knowledge' | 'documents' | 'settings' | 'dashboard';
  chatLayout: 'default' | 'wide' | 'focus';
  documentView: 'grid' | 'list' | 'detail';
  searchOpen: boolean;
  commandPaletteOpen: boolean;
  keyboardShortcutsEnabled: boolean;
  animations: boolean;
  density: 'comfortable' | 'compact' | 'spacious';
}

const initialState: UIState = {
  sidebarOpen: true,
  sidebarCollapsed: false,
  rightPanelOpen: false,
  fullscreen: false,
  loading: {
    global: false,
    tasks: {},
  },
  toasts: [],
  modals: [],
  drawer: {
    open: false,
    anchor: 'left',
  },
  breadcrumbs: [],
  activeView: 'chat',
  chatLayout: 'default',
  documentView: 'grid',
  searchOpen: false,
  commandPaletteOpen: false,
  keyboardShortcutsEnabled: true,
  animations: true,
  density: 'comfortable',
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    toggleSidebar: (state) => {
      state.sidebarOpen = !state.sidebarOpen;
    },
    setSidebarOpen: (state, action: PayloadAction<boolean>) => {
      state.sidebarOpen = action.payload;
    },
    toggleSidebarCollapse: (state) => {
      state.sidebarCollapsed = !state.sidebarCollapsed;
    },
    toggleRightPanel: (state) => {
      state.rightPanelOpen = !state.rightPanelOpen;
    },
    setRightPanelOpen: (state, action: PayloadAction<boolean>) => {
      state.rightPanelOpen = action.payload;
    },
    toggleFullscreen: (state) => {
      state.fullscreen = !state.fullscreen;
    },
    setGlobalLoading: (state, action: PayloadAction<boolean>) => {
      state.loading.global = action.payload;
    },
    setTaskLoading: (state, action: PayloadAction<{ taskId: string; loading: boolean }>) => {
      if (action.payload.loading) {
        state.loading.tasks[action.payload.taskId] = true;
      } else {
        delete state.loading.tasks[action.payload.taskId];
      }
    },
    showToast: (state, action: PayloadAction<Omit<Toast, 'id'>>) => {
      const toast: Toast = {
        ...action.payload,
        id: Date.now().toString(),
        duration: action.payload.duration || 5000,
      };
      state.toasts.push(toast);
    },
    hideToast: (state, action: PayloadAction<string>) => {
      state.toasts = state.toasts.filter((toast) => toast.id !== action.payload);
    },
    clearToasts: (state) => {
      state.toasts = [];
    },
    showModal: (state, action: PayloadAction<Omit<Modal, 'id'>>) => {
      const modal: Modal = {
        ...action.payload,
        id: Date.now().toString(),
      };
      state.modals.push(modal);
    },
    hideModal: (state, action: PayloadAction<string>) => {
      state.modals = state.modals.filter((modal) => modal.id !== action.payload);
    },
    clearModals: (state) => {
      state.modals = [];
    },
    openDrawer: (
      state,
      action: PayloadAction<{
        anchor?: Drawer['anchor'];
        component?: React.ComponentType;
        props?: Record<string, any>;
      }>
    ) => {
      state.drawer = {
        open: true,
        anchor: action.payload.anchor || 'left',
        component: action.payload.component,
        props: action.payload.props,
      };
    },
    closeDrawer: (state) => {
      state.drawer.open = false;
    },
    setBreadcrumbs: (state, action: PayloadAction<UIState['breadcrumbs']>) => {
      state.breadcrumbs = action.payload;
    },
    addBreadcrumb: (state, action: PayloadAction<{ label: string; path?: string }>) => {
      state.breadcrumbs.push(action.payload);
    },
    setActiveView: (state, action: PayloadAction<UIState['activeView']>) => {
      state.activeView = action.payload;
    },
    setChatLayout: (state, action: PayloadAction<UIState['chatLayout']>) => {
      state.chatLayout = action.payload;
    },
    setDocumentView: (state, action: PayloadAction<UIState['documentView']>) => {
      state.documentView = action.payload;
    },
    toggleSearch: (state) => {
      state.searchOpen = !state.searchOpen;
    },
    setSearchOpen: (state, action: PayloadAction<boolean>) => {
      state.searchOpen = action.payload;
    },
    toggleCommandPalette: (state) => {
      state.commandPaletteOpen = !state.commandPaletteOpen;
    },
    setCommandPaletteOpen: (state, action: PayloadAction<boolean>) => {
      state.commandPaletteOpen = action.payload;
    },
    toggleKeyboardShortcuts: (state) => {
      state.keyboardShortcutsEnabled = !state.keyboardShortcutsEnabled;
    },
    toggleAnimations: (state) => {
      state.animations = !state.animations;
    },
    setDensity: (state, action: PayloadAction<UIState['density']>) => {
      state.density = action.payload;
    },
  },
});

export const {
  toggleSidebar,
  setSidebarOpen,
  toggleSidebarCollapse,
  toggleRightPanel,
  setRightPanelOpen,
  toggleFullscreen,
  setGlobalLoading,
  setTaskLoading,
  showToast,
  hideToast,
  clearToasts,
  showModal,
  hideModal,
  clearModals,
  openDrawer,
  closeDrawer,
  setBreadcrumbs,
  addBreadcrumb,
  setActiveView,
  setChatLayout,
  setDocumentView,
  toggleSearch,
  setSearchOpen,
  toggleCommandPalette,
  setCommandPaletteOpen,
  toggleKeyboardShortcuts,
  toggleAnimations,
  setDensity,
} = uiSlice.actions;
export default uiSlice.reducer;