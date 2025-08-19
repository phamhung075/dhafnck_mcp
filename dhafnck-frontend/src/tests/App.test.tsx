import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import App from '../App';

// Mock the auth context
jest.mock('../contexts/AuthContext', () => ({
  AuthContext: {
    Provider: ({ children }: { children: React.ReactNode }) => children,
    Consumer: ({ children }: any) => children({
      user: { id: '123', username: 'testuser', email: 'test@example.com', roles: ['user'] },
      isAuthenticated: true,
      login: jest.fn(),
      logout: jest.fn(),
    })
  }
}));

// Mock the auth components
jest.mock('../components/auth', () => ({
  AuthWrapper: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  LoginForm: () => <div>Login Form</div>,
  SignupForm: () => <div>Signup Form</div>,
  EmailVerification: () => <div>Email Verification</div>,
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// Mock the components
jest.mock('../components/Header', () => ({
  Header: () => <header>Test Header</header>
}));

jest.mock('../components/AppLayout', () => ({
  AppLayout: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="app-layout">{children}</div>
  )
}));

jest.mock('../pages/Profile', () => ({
  Profile: () => <div>Profile Page</div>
}));

jest.mock('../components/ProjectList', () => ({
  default: ({ onSelect }: any) => (
    <div data-testid="project-list">
      <button onClick={() => onSelect('project1', 'branch1')}>Select Project</button>
    </div>
  )
}));

jest.mock('../components/LazyTaskList', () => ({
  default: ({ projectId, taskTreeId }: any) => (
    <div data-testid="task-list">
      Task List for {projectId} - {taskTreeId}
    </div>
  )
}));

describe('App', () => {
  beforeEach(() => {
    // Reset window.location before each test
    window.history.pushState({}, '', '/');
  });

  it('renders without crashing', () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );
  });

  it('redirects to dashboard from root path', async () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(window.location.pathname).toBe('/dashboard');
    });
  });

  it('renders login form on /login route', () => {
    window.history.pushState({}, '', '/login');
    
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );

    expect(screen.getByText('Login Form')).toBeInTheDocument();
  });

  it('renders signup form on /signup route', () => {
    window.history.pushState({}, '', '/signup');
    
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );

    expect(screen.getByText('Signup Form')).toBeInTheDocument();
  });

  it('renders email verification on /auth/verify route', () => {
    window.history.pushState({}, '', '/auth/verify');
    
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );

    expect(screen.getByText('Email Verification')).toBeInTheDocument();
  });

  it('renders dashboard with header and project list on /dashboard route', () => {
    window.history.pushState({}, '', '/dashboard');
    
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );

    expect(screen.getByText('Test Header')).toBeInTheDocument();
    expect(screen.getByTestId('project-list')).toBeInTheDocument();
    expect(screen.getByText('Select a project and branch to see tasks.')).toBeInTheDocument();
  });

  it('renders profile page with AppLayout on /profile route', () => {
    window.history.pushState({}, '', '/profile');
    
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );

    expect(screen.getByTestId('app-layout')).toBeInTheDocument();
    expect(screen.getByText('Profile Page')).toBeInTheDocument();
  });
});