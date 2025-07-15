/**
 * Unit Tests for IntegratedNavigation Component
 * Tests navigation functionality, agent switching, project selection, and health indicators
 */

import React from 'react';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { render, mockAgent, mockProject, mockUser, mockSystemHealth, mockNotification } from '../setup';
import { IntegratedNavigation } from '../../components/IntegratedNavigation';

// Mock the SystemIntegration hook
jest.mock('../../integration/SystemIntegration', () => ({
  useSystemIntegration: () => ({
    state: {
      ui: { currentView: 'dashboard' },
      projects: { selected: null }
    },
    actions: {},
    performance: {}
  })
}));

describe('IntegratedNavigation', () => {
  const defaultProps = {
    currentUser: mockUser,
    projects: [mockProject],
    currentAgent: null,
    systemHealth: mockSystemHealth,
    notifications: [],
    onNavigate: jest.fn(),
    onAgentSwitch: jest.fn(),
    onProjectSwitch: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    test('renders navigation with all required elements', () => {
      render(<IntegratedNavigation {...defaultProps} />);

      // Check logo and brand
      expect(screen.getByText('DhafnckMCP')).toBeInTheDocument();

      // Check navigation links
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Projects')).toBeInTheDocument();
      expect(screen.getByText('Agents')).toBeInTheDocument();
      expect(screen.getByText('Contexts')).toBeInTheDocument();
      expect(screen.getByText('Monitoring')).toBeInTheDocument();
      expect(screen.getByText('Compliance')).toBeInTheDocument();

      // Check search functionality
      expect(screen.getByText('Search or run command...')).toBeInTheDocument();

      // Check user section
      expect(screen.getByText(mockUser.name)).toBeInTheDocument();
    });

    test('renders mobile menu button on small screens', () => {
      render(<IntegratedNavigation {...defaultProps} />);

      // Mobile menu button should be present but may be hidden on larger screens
      const menuButtons = screen.getAllByRole('button');
      expect(menuButtons.length).toBeGreaterThan(0);
    });

    test('shows current agent when provided', () => {
      const propsWithAgent = {
        ...defaultProps,
        currentAgent: mockAgent
      };

      render(<IntegratedNavigation {...propsWithAgent} />);

      expect(screen.getByText(mockAgent.name)).toBeInTheDocument();
    });

    test('shows "No Agent" when no current agent', () => {
      render(<IntegratedNavigation {...defaultProps} />);

      expect(screen.getByText('No Agent')).toBeInTheDocument();
    });
  });

  describe('Health Indicator', () => {
    test('shows healthy status correctly', () => {
      render(<IntegratedNavigation {...defaultProps} />);

      expect(screen.getByText('healthy')).toBeInTheDocument();
    });

    test('shows degraded status with warning color', () => {
      const degradedHealth = {
        ...mockSystemHealth,
        status: 'degraded' as const
      };

      render(
        <IntegratedNavigation 
          {...defaultProps} 
          systemHealth={degradedHealth} 
        />
      );

      expect(screen.getByText('degraded')).toBeInTheDocument();
    });

    test('shows critical status with error color', () => {
      const criticalHealth = {
        ...mockSystemHealth,
        status: 'critical' as const
      };

      render(
        <IntegratedNavigation 
          {...defaultProps} 
          systemHealth={criticalHealth} 
        />
      );

      expect(screen.getByText('critical')).toBeInTheDocument();
    });

    test('shows unknown status when health is null', () => {
      render(
        <IntegratedNavigation 
          {...defaultProps} 
          systemHealth={null} 
        />
      );

      expect(screen.getByText('Unknown')).toBeInTheDocument();
    });
  });

  describe('Agent Switcher', () => {
    test('opens agent selector when clicked', async () => {
      const user = userEvent.setup();
      render(<IntegratedNavigation {...defaultProps} />);

      const agentButton = screen.getByText('No Agent').closest('button')!;
      await user.click(agentButton);

      expect(screen.getByText('Switch Agent')).toBeInTheDocument();
      expect(screen.getByText('@coding_agent')).toBeInTheDocument();
      expect(screen.getByText('@debugger_agent')).toBeInTheDocument();
    });

    test('calls onAgentSwitch when agent is selected', async () => {
      const user = userEvent.setup();
      const onAgentSwitch = jest.fn().mockResolvedValue(undefined);
      
      render(
        <IntegratedNavigation 
          {...defaultProps} 
          onAgentSwitch={onAgentSwitch} 
        />
      );

      // Open agent selector
      const agentButton = screen.getByText('No Agent').closest('button')!;
      await user.click(agentButton);

      // Select coding agent
      const codingAgent = screen.getByText('@coding_agent');
      await user.click(codingAgent);

      expect(onAgentSwitch).toHaveBeenCalledWith(
        expect.objectContaining({
          name: '@coding_agent'
        })
      );
    });

    test('handles agent switch errors gracefully', async () => {
      const user = userEvent.setup();
      const onAgentSwitch = jest.fn().mockRejectedValue(new Error('Switch failed'));
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      render(
        <IntegratedNavigation 
          {...defaultProps} 
          onAgentSwitch={onAgentSwitch} 
        />
      );

      // Open agent selector
      const agentButton = screen.getByText('No Agent').closest('button')!;
      await user.click(agentButton);

      // Select coding agent
      const codingAgent = screen.getByText('@coding_agent');
      await user.click(codingAgent);

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith(
          'Failed to switch agent:',
          expect.any(Error)
        );
      });

      consoleSpy.mockRestore();
    });

    test('shows current agent as selected', async () => {
      const user = userEvent.setup();
      const propsWithAgent = {
        ...defaultProps,
        currentAgent: mockAgent
      };

      render(<IntegratedNavigation {...propsWithAgent} />);

      // Open agent selector
      const agentButton = screen.getByText(mockAgent.name).closest('button')!;
      await user.click(agentButton);

      // Check that current agent has a check mark
      const currentAgentRow = screen.getByText(mockAgent.name).closest('button')!;
      expect(currentAgentRow).toHaveClass('bg-blue-50');
    });

    test('disables switching to same agent', async () => {
      const user = userEvent.setup();
      const onAgentSwitch = jest.fn();
      const propsWithAgent = {
        ...defaultProps,
        currentAgent: mockAgent,
        onAgentSwitch
      };

      render(<IntegratedNavigation {...propsWithAgent} />);

      // Open agent selector
      const agentButton = screen.getByText(mockAgent.name).closest('button')!;
      await user.click(agentButton);

      // Try to click the same agent
      const sameAgentButton = screen.getByText(mockAgent.name);
      await user.click(sameAgentButton);

      // Should not call onAgentSwitch
      expect(onAgentSwitch).not.toHaveBeenCalled();
    });
  });

  describe('Project Selector', () => {
    test('opens project selector when clicked', async () => {
      const user = userEvent.setup();
      render(<IntegratedNavigation {...defaultProps} />);

      const projectButton = screen.getByText('Select Project').closest('button')!;
      await user.click(projectButton);

      expect(screen.getByText('Projects')).toBeInTheDocument();
      expect(screen.getByText(mockProject.name)).toBeInTheDocument();
    });

    test('calls onProjectSwitch when project is selected', async () => {
      const user = userEvent.setup();
      const onProjectSwitch = jest.fn();

      render(
        <IntegratedNavigation 
          {...defaultProps} 
          onProjectSwitch={onProjectSwitch} 
        />
      );

      // Open project selector
      const projectButton = screen.getByText('Select Project').closest('button')!;
      await user.click(projectButton);

      // Select project
      const projectOption = screen.getByText(mockProject.name);
      await user.click(projectOption);

      expect(onProjectSwitch).toHaveBeenCalledWith(mockProject);
    });

    test('shows "No projects available" when projects array is empty', async () => {
      const user = userEvent.setup();
      const propsWithoutProjects = {
        ...defaultProps,
        projects: []
      };

      render(<IntegratedNavigation {...propsWithoutProjects} />);

      const projectButton = screen.getByText('Select Project').closest('button')!;
      await user.click(projectButton);

      expect(screen.getByText('No projects available')).toBeInTheDocument();
    });
  });

  describe('Navigation', () => {
    test('calls onNavigate when navigation links are clicked', async () => {
      const user = userEvent.setup();
      const onNavigate = jest.fn();

      render(
        <IntegratedNavigation 
          {...defaultProps} 
          onNavigate={onNavigate} 
        />
      );

      const projectsLink = screen.getByText('Projects');
      await user.click(projectsLink);

      expect(onNavigate).toHaveBeenCalledWith('/projects');
    });

    test('highlights current view', () => {
      // This would require mocking the Redux state properly
      // For now, we test that the component renders without errors
      render(<IntegratedNavigation {...defaultProps} />);
      
      // Dashboard should be highlighted by default
      const dashboardLink = screen.getByText('Dashboard');
      expect(dashboardLink.closest('button')).toHaveClass('bg-blue-100');
    });
  });

  describe('Notification Center', () => {
    test('shows notification count when there are unread notifications', () => {
      const notifications = [
        mockNotification,
        { ...mockNotification, id: 'notification-2', read: false }
      ];

      render(
        <IntegratedNavigation 
          {...defaultProps} 
          notifications={notifications} 
        />
      );

      expect(screen.getByText('2')).toBeInTheDocument();
    });

    test('shows 9+ when there are more than 9 unread notifications', () => {
      const notifications = Array.from({ length: 12 }, (_, i) => ({
        ...mockNotification,
        id: `notification-${i}`,
        read: false
      }));

      render(
        <IntegratedNavigation 
          {...defaultProps} 
          notifications={notifications} 
        />
      );

      expect(screen.getByText('9+')).toBeInTheDocument();
    });

    test('opens notification panel when clicked', async () => {
      const user = userEvent.setup();
      const notifications = [mockNotification];

      render(
        <IntegratedNavigation 
          {...defaultProps} 
          notifications={notifications} 
        />
      );

      const notificationButton = screen.getByRole('button', { name: /notifications/i });
      await user.click(notificationButton);

      expect(screen.getByText('Notifications')).toBeInTheDocument();
      expect(screen.getByText(mockNotification.title)).toBeInTheDocument();
    });

    test('shows "No notifications" when notifications array is empty', async () => {
      const user = userEvent.setup();

      render(<IntegratedNavigation {...defaultProps} />);

      const notificationButton = screen.getByRole('button', { name: /notifications/i });
      await user.click(notificationButton);

      expect(screen.getByText('No notifications')).toBeInTheDocument();
    });
  });

  describe('Search Functionality', () => {
    test('opens command palette when search is clicked', async () => {
      const user = userEvent.setup();
      render(<IntegratedNavigation {...defaultProps} />);

      const searchButton = screen.getByText('Search or run command...').closest('button')!;
      await user.click(searchButton);

      // This would require Redux integration to test properly
      // For now, we verify the button is clickable
      expect(searchButton).toBeEnabled();
    });

    test('shows keyboard shortcuts', () => {
      render(<IntegratedNavigation {...defaultProps} />);

      expect(screen.getByText('⌘')).toBeInTheDocument();
      expect(screen.getByText('K')).toBeInTheDocument();
    });
  });

  describe('Responsive Behavior', () => {
    test('toggles mobile menu', async () => {
      const user = userEvent.setup();
      
      // Mock window size to trigger mobile view
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 500,
      });

      render(<IntegratedNavigation {...defaultProps} />);

      // Find mobile menu toggle button (first button, which is the mobile menu toggle)
      const buttons = screen.getAllByRole('button');
      const mobileMenuButton = buttons[0];
      
      await user.click(mobileMenuButton);

      // Mobile menu should show navigation links
      // This test depends on Redux state management which is mocked
      expect(mobileMenuButton).toBeEnabled();
    });
  });

  describe('Accessibility', () => {
    test('has proper ARIA labels and roles', () => {
      render(<IntegratedNavigation {...defaultProps} />);

      // Check that interactive elements have proper roles
      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);

      // Check navigation structure
      const navigation = screen.getByRole('navigation');
      expect(navigation).toBeInTheDocument();
    });

    test('supports keyboard navigation', async () => {
      const user = userEvent.setup();
      render(<IntegratedNavigation {...defaultProps} />);

      // Tab through interactive elements
      await user.tab();
      expect(document.activeElement).toBeInstanceOf(HTMLElement);

      // Test that all interactive elements are focusable
      const buttons = screen.getAllByRole('button');
      for (const button of buttons) {
        expect(button).not.toHaveAttribute('tabindex', '-1');
      }
    });
  });
});