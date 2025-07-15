import { configureStore, createSlice, PayloadAction } from '@reduxjs/toolkit';
import { TypedUseSelectorHook, useDispatch, useSelector } from 'react-redux';
import type {
  SystemHealthStatus,
  ComplianceStatus,
  ConnectionStatus,
  Notification,
  LoadingState,
  ErrorState,
  User,
  Agent,
  Project,
  GitBranch,
  Task,
  HierarchicalContext,
  Rule,
  UserPreferences,
  ActivityItem,
  ViewType,
  Modal,
  UINotification
} from '../types/application';

// Global Application State
interface GlobalState {
  system: {
    health: SystemHealthStatus | null;
    compliance: ComplianceStatus | null;
    connection: ConnectionStatus;
    notifications: Notification[];
    loading: LoadingState;
    errors: ErrorState;
  };
  
  session: {
    currentUser: User | null;
    currentAgent: Agent | null;
    selectedProject: Project | null;
    selectedBranch: GitBranch | null;
    selectedContext: HierarchicalContext | null;
    preferences: UserPreferences;
    recentActivity: ActivityItem[];
  };
  
  data: {
    projects: Project[];
    branches: Record<string, GitBranch[]>;
    tasks: Record<string, Task[]>;
    agents: Record<string, Agent[]>;
    contexts: HierarchicalContext[];
    rules: Rule[];
  };
  
  ui: {
    currentView: ViewType;
    sidebarOpen: boolean;
    theme: 'light' | 'dark' | 'auto';
    modalStack: Modal[];
    commandPaletteOpen: boolean;
    notifications: UINotification[];
  };
}

// System Slice
const systemSlice = createSlice({
  name: 'system',
  initialState: {
    health: null,
    compliance: null,
    connection: { status: 'unknown', latency: 0, uptime_percentage: 0, active_connections: 0, last_check: '', error_rate: 0 },
    notifications: [],
    loading: {},
    errors: {}
  } as GlobalState['system'],
  reducers: {
    setSystemHealth: (state, action: PayloadAction<SystemHealthStatus>) => {
      state.health = action.payload;
    },
    setComplianceStatus: (state, action: PayloadAction<ComplianceStatus>) => {
      state.compliance = action.payload;
    },
    setConnectionStatus: (state, action: PayloadAction<ConnectionStatus>) => {
      state.connection = action.payload;
    },
    addNotification: (state, action: PayloadAction<Notification>) => {
      state.notifications.unshift(action.payload);
      if (state.notifications.length > 100) {
        state.notifications = state.notifications.slice(0, 100);
      }
    },
    markNotificationRead: (state, action: PayloadAction<string>) => {
      const notification = state.notifications.find(n => n.id === action.payload);
      if (notification) {
        notification.read = true;
      }
    },
    clearNotifications: (state) => {
      state.notifications = [];
    },
    setLoading: (state, action: PayloadAction<{ key: string; loading: boolean }>) => {
      state.loading[action.payload.key] = action.payload.loading;
    },
    setError: (state, action: PayloadAction<{ key: string; error: string | null }>) => {
      if (action.payload.error) {
        state.errors[action.payload.key] = action.payload.error;
      } else {
        delete state.errors[action.payload.key];
      }
    },
    clearError: (state, action: PayloadAction<string>) => {
      delete state.errors[action.payload];
    },
    setProjects: (state, action: PayloadAction<Project[]>) => {
      // This action belongs in dataSlice, keeping here for compatibility
    }
  }
});

// Session Slice
const sessionSlice = createSlice({
  name: 'session',
  initialState: {
    currentUser: null,
    currentAgent: null,
    selectedProject: null,
    selectedBranch: null,
    selectedContext: null,
    preferences: {
      theme: 'auto',
      notifications: true,
      autoRefresh: true,
      refreshInterval: 30000,
      sidebarCollapsed: false,
      defaultView: 'dashboard'
    },
    recentActivity: []
  } as GlobalState['session'],
  reducers: {
    setCurrentUser: (state, action: PayloadAction<User | null>) => {
      state.currentUser = action.payload;
    },
    setCurrentAgent: (state, action: PayloadAction<Agent | null>) => {
      state.currentAgent = action.payload;
      if (action.payload) {
        state.recentActivity.unshift({
          id: Date.now().toString(),
          type: 'agent_switch',
          description: `Switched to ${action.payload.name}`,
          timestamp: new Date().toISOString()
        });
        // Keep only last 50 activities
        if (state.recentActivity.length > 50) {
          state.recentActivity = state.recentActivity.slice(0, 50);
        }
      }
    },
    setSelectedProject: (state, action: PayloadAction<Project | null>) => {
      state.selectedProject = action.payload;
      state.selectedBranch = null; // Clear branch when project changes
      if (action.payload) {
        state.recentActivity.unshift({
          id: Date.now().toString(),
          type: 'project_select',
          description: `Selected project ${action.payload.name}`,
          timestamp: new Date().toISOString()
        });
      }
    },
    setSelectedBranch: (state, action: PayloadAction<GitBranch | null>) => {
      state.selectedBranch = action.payload;
      if (action.payload) {
        state.recentActivity.unshift({
          id: Date.now().toString(),
          type: 'branch_select',
          description: `Selected branch ${action.payload.git_branch_name}`,
          timestamp: new Date().toISOString()
        });
      }
    },
    setSelectedContext: (state, action: PayloadAction<HierarchicalContext | null>) => {
      state.selectedContext = action.payload;
    },
    updatePreferences: (state, action: PayloadAction<Partial<UserPreferences>>) => {
      state.preferences = { ...state.preferences, ...action.payload };
    },
    addActivity: (state, action: PayloadAction<ActivityItem>) => {
      state.recentActivity.unshift(action.payload);
      if (state.recentActivity.length > 50) {
        state.recentActivity = state.recentActivity.slice(0, 50);
      }
    }
  }
});

// Data Slice
const dataSlice = createSlice({
  name: 'data',
  initialState: {
    projects: [],
    branches: {},
    tasks: {},
    agents: {},
    contexts: [],
    rules: []
  } as GlobalState['data'],
  reducers: {
    setProjects: (state, action: PayloadAction<Project[]>) => {
      state.projects = action.payload;
    },
    addProject: (state, action: PayloadAction<Project>) => {
      state.projects.push(action.payload);
    },
    updateProject: (state, action: PayloadAction<{ id: string; updates: Partial<Project> }>) => {
      const index = state.projects.findIndex(p => p.id === action.payload.id);
      if (index !== -1) {
        state.projects[index] = { ...state.projects[index], ...action.payload.updates };
      }
    },
    setBranches: (state, action: PayloadAction<{ projectId: string; branches: GitBranch[] }>) => {
      state.branches[action.payload.projectId] = action.payload.branches;
    },
    addBranch: (state, action: PayloadAction<{ projectId: string; branch: GitBranch }>) => {
      if (!state.branches[action.payload.projectId]) {
        state.branches[action.payload.projectId] = [];
      }
      state.branches[action.payload.projectId].push(action.payload.branch);
    },
    setTasks: (state, action: PayloadAction<{ branchId: string; tasks: Task[] }>) => {
      state.tasks[action.payload.branchId] = action.payload.tasks;
    },
    addTask: (state, action: PayloadAction<{ branchId: string; task: Task }>) => {
      if (!state.tasks[action.payload.branchId]) {
        state.tasks[action.payload.branchId] = [];
      }
      state.tasks[action.payload.branchId].push(action.payload.task);
    },
    updateTask: (state, action: PayloadAction<{ branchId: string; taskId: string; updates: Partial<Task> }>) => {
      const tasks = state.tasks[action.payload.branchId];
      if (tasks) {
        const taskIndex = tasks.findIndex(t => t.id === action.payload.taskId);
        if (taskIndex !== -1) {
          tasks[taskIndex] = { ...tasks[taskIndex], ...action.payload.updates };
        }
      }
    },
    removeTask: (state, action: PayloadAction<{ branchId: string; taskId: string }>) => {
      const tasks = state.tasks[action.payload.branchId];
      if (tasks) {
        state.tasks[action.payload.branchId] = tasks.filter(t => t.id !== action.payload.taskId);
      }
    },
    setAgents: (state, action: PayloadAction<{ projectId: string; agents: Agent[] }>) => {
      state.agents[action.payload.projectId] = action.payload.agents;
    },
    addAgent: (state, action: PayloadAction<{ projectId: string; agent: Agent }>) => {
      if (!state.agents[action.payload.projectId]) {
        state.agents[action.payload.projectId] = [];
      }
      state.agents[action.payload.projectId].push(action.payload.agent);
    },
    updateAgent: (state, action: PayloadAction<{ projectId: string; agentId: string; updates: Partial<Agent> }>) => {
      const agents = state.agents[action.payload.projectId];
      if (agents) {
        const agentIndex = agents.findIndex(a => a.id === action.payload.agentId);
        if (agentIndex !== -1) {
          agents[agentIndex] = { ...agents[agentIndex], ...action.payload.updates };
        }
      }
    },
    setContexts: (state, action: PayloadAction<HierarchicalContext[]>) => {
      state.contexts = action.payload;
    },
    addContext: (state, action: PayloadAction<HierarchicalContext>) => {
      state.contexts.push(action.payload);
    },
    updateContext: (state, action: PayloadAction<{ id: string; updates: Partial<HierarchicalContext> }>) => {
      const index = state.contexts.findIndex(c => c.id === action.payload.id);
      if (index !== -1) {
        state.contexts[index] = { ...state.contexts[index], ...action.payload.updates };
      }
    },
    setRules: (state, action: PayloadAction<Rule[]>) => {
      state.rules = action.payload;
    }
  }
});

// UI Slice
const uiSlice = createSlice({
  name: 'ui',
  initialState: {
    currentView: 'dashboard',
    sidebarOpen: true,
    theme: 'auto',
    modalStack: [],
    commandPaletteOpen: false,
    notifications: []
  } as GlobalState['ui'],
  reducers: {
    setCurrentView: (state, action: PayloadAction<ViewType>) => {
      state.currentView = action.payload;
    },
    setSidebarOpen: (state, action: PayloadAction<boolean>) => {
      state.sidebarOpen = action.payload;
    },
    toggleSidebar: (state) => {
      state.sidebarOpen = !state.sidebarOpen;
    },
    setTheme: (state, action: PayloadAction<'light' | 'dark' | 'auto'>) => {
      state.theme = action.payload;
    },
    pushModal: (state, action: PayloadAction<Modal>) => {
      state.modalStack.push(action.payload);
    },
    popModal: (state) => {
      state.modalStack.pop();
    },
    clearModals: (state) => {
      state.modalStack = [];
    },
    setCommandPaletteOpen: (state, action: PayloadAction<boolean>) => {
      state.commandPaletteOpen = action.payload;
    },
    toggleCommandPalette: (state) => {
      state.commandPaletteOpen = !state.commandPaletteOpen;
    },
    addUINotification: (state, action: PayloadAction<UINotification>) => {
      // Remove any existing notification with the same ID to prevent duplicates
      state.notifications = state.notifications.filter(n => n.id !== action.payload.id);
      // Add the new notification at the beginning
      state.notifications.unshift(action.payload);
      if (state.notifications.length > 10) {
        state.notifications = state.notifications.slice(0, 10);
      }
    },
    removeUINotification: (state, action: PayloadAction<string>) => {
      state.notifications = state.notifications.filter(n => n.id !== action.payload);
    },
    clearUINotifications: (state) => {
      state.notifications = [];
    }
  }
});

// Store Configuration
export const store = configureStore({
  reducer: {
    system: systemSlice.reducer,
    session: sessionSlice.reducer,
    data: dataSlice.reducer,
    ui: uiSlice.reducer
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST'],
        ignoredActionsPaths: ['payload.actions'], // For notification actions
        ignoredPaths: ['ui.notifications.actions'] // For notification actions in state
      }
    })
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;

// Action Creators
export const systemActions = systemSlice.actions;
export const sessionActions = sessionSlice.actions;
export const dataActions = dataSlice.actions;
export const uiActions = uiSlice.actions;