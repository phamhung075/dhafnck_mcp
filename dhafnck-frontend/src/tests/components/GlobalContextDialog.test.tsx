import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import GlobalContextDialog from '../../components/GlobalContextDialog';
import { useAuthenticatedFetch } from '../../hooks/useAuthenticatedFetch';
import { ThemeProvider } from '../../contexts/ThemeContext';

// Mock dependencies
jest.mock('../../hooks/useAuthenticatedFetch', () => ({
  useAuthenticatedFetch: jest.fn(),
}));

jest.mock('@mui/icons-material/InfoOutlined', () => {
  return function InfoOutlined() {
    return <div data-testid="info-icon">InfoOutlined</div>;
  };
});

// Mock dialog components
jest.mock('@mui/material', () => {
  const actual = jest.requireActual('@mui/material');
  return {
    ...actual,
    Dialog: ({ children, open }: any) => (
      open ? <div data-testid="dialog">{children}</div> : null
    ),
    DialogTitle: ({ children }: any) => <div>{children}</div>,
    DialogContent: ({ children }: any) => <div>{children}</div>,
    DialogActions: ({ children }: any) => <div>{children}</div>,
    IconButton: ({ children, onClick, ...props }: any) => (
      <button onClick={onClick} {...props}>{children}</button>
    ),
    Button: ({ children, onClick, ...props }: any) => (
      <button onClick={onClick} {...props}>{children}</button>
    ),
    CircularProgress: () => <div data-testid="loading">Loading...</div>,
    Box: ({ children }: any) => <div>{children}</div>,
    Typography: ({ children }: any) => <div>{children}</div>,
  };
});

const mockFetch = jest.mocked(useAuthenticatedFetch);

const mockContext = {
  features: {
    authentication: true,
    task_management: true,
    rule_engine: true,
  },
  version: '1.0.0',
  debug_mode: false,
  environment: 'test',
};

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider>
      {component}
    </ThemeProvider>
  );
};

describe('GlobalContextDialog', () => {
  let mockApiCall: jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
    mockApiCall = jest.fn();
    mockFetch.mockReturnValue(mockApiCall);
  });

  it('renders the dialog trigger button', () => {
    mockApiCall.mockResolvedValue({ data: mockContext });
    renderWithTheme(<GlobalContextDialog />);
    
    const button = screen.getByRole('button', { name: /global context/i });
    expect(button).toBeInTheDocument();
    expect(screen.getByTestId('info-icon')).toBeInTheDocument();
  });

  it('opens dialog when button is clicked', async () => {
    mockApiCall.mockResolvedValue({ data: mockContext });
    renderWithTheme(<GlobalContextDialog />);
    
    const button = screen.getByRole('button', { name: /global context/i });
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByTestId('dialog')).toBeInTheDocument();
      expect(screen.getByText(/Global Context/)).toBeInTheDocument();
    });
  });

  it('fetches and displays global context data', async () => {
    mockApiCall.mockResolvedValue({ data: mockContext });
    renderWithTheme(<GlobalContextDialog />);
    
    const button = screen.getByRole('button', { name: /global context/i });
    fireEvent.click(button);

    await waitFor(() => {
      expect(mockApiCall).toHaveBeenCalledWith(
        `/api/v2/context/manage_context`,
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            action: 'get',
            level: 'global',
            context_id: 'global_singleton',
            include_inherited: true,
          }),
        })
      );
    });

    await waitFor(() => {
      // Check if context data is displayed
      expect(screen.getByText(/authentication/)).toBeInTheDocument();
      expect(screen.getByText(/task_management/)).toBeInTheDocument();
      expect(screen.getByText(/rule_engine/)).toBeInTheDocument();
      expect(screen.getByText(/1.0.0/)).toBeInTheDocument();
    });
  });

  it('shows loading state while fetching data', async () => {
    mockApiCall.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));
    renderWithTheme(<GlobalContextDialog />);
    
    const button = screen.getByRole('button', { name: /global context/i });
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByTestId('loading')).toBeInTheDocument();
    });
  });

  it('handles error when fetching data fails', async () => {
    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
    mockApiCall.mockRejectedValue(new Error('Network error'));
    
    renderWithTheme(<GlobalContextDialog />);
    
    const button = screen.getByRole('button', { name: /global context/i });
    fireEvent.click(button);

    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Failed to fetch global context:',
        expect.any(Error)
      );
    });

    consoleErrorSpy.mockRestore();
  });

  it('handles empty or null context data', async () => {
    mockApiCall.mockResolvedValue({ data: null });
    renderWithTheme(<GlobalContextDialog />);
    
    const button = screen.getByRole('button', { name: /global context/i });
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText(/No global context available/)).toBeInTheDocument();
    });
  });

  it('closes dialog when close button is clicked', async () => {
    mockApiCall.mockResolvedValue({ data: mockContext });
    renderWithTheme(<GlobalContextDialog />);
    
    const button = screen.getByRole('button', { name: /global context/i });
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByTestId('dialog')).toBeInTheDocument();
    });

    const closeButton = screen.getByRole('button', { name: /close/i });
    fireEvent.click(closeButton);

    await waitFor(() => {
      expect(screen.queryByTestId('dialog')).not.toBeInTheDocument();
    });
  });

  it('renders with custom className', () => {
    mockApiCall.mockResolvedValue({ data: mockContext });
    renderWithTheme(<GlobalContextDialog className="custom-class" />);
    
    const button = screen.getByRole('button', { name: /global context/i });
    expect(button).toHaveClass('custom-class');
  });

  it('displays complex nested context data correctly', async () => {
    const complexContext = {
      ...mockContext,
      nested: {
        level1: {
          level2: {
            value: 'deep value',
          },
        },
      },
      array: ['item1', 'item2', 'item3'],
    };
    
    mockApiCall.mockResolvedValue({ data: complexContext });
    renderWithTheme(<GlobalContextDialog />);
    
    const button = screen.getByRole('button', { name: /global context/i });
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText(/deep value/)).toBeInTheDocument();
      expect(screen.getByText(/item1/)).toBeInTheDocument();
      expect(screen.getByText(/item2/)).toBeInTheDocument();
    });
  });

  it('re-fetches data when dialog is reopened', async () => {
    mockApiCall.mockResolvedValue({ data: mockContext });
    renderWithTheme(<GlobalContextDialog />);
    
    // Open dialog
    const button = screen.getByRole('button', { name: /global context/i });
    fireEvent.click(button);

    await waitFor(() => {
      expect(mockApiCall).toHaveBeenCalledTimes(1);
    });

    // Close dialog
    const closeButton = screen.getByRole('button', { name: /close/i });
    fireEvent.click(closeButton);

    // Reopen dialog
    fireEvent.click(button);

    await waitFor(() => {
      expect(mockApiCall).toHaveBeenCalledTimes(2);
    });
  });
});