import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { GlobalContextDialog } from '../../components/GlobalContextDialog';
import { api } from '../../api';

// Mock the API module
jest.mock('../../api', () => ({
  api: {
    updateGlobalContext: jest.fn(),
    fetchGlobalContext: jest.fn(),
  },
}));

// Mock shadcn/ui components
jest.mock('../../components/ui/dialog', () => ({
  Dialog: ({ open, children }: any) => open ? <div data-testid="dialog">{children}</div> : null,
  DialogContent: ({ children, className }: any) => <div className={className}>{children}</div>,
  DialogHeader: ({ children }: any) => <div>{children}</div>,
  DialogTitle: ({ children }: any) => <h2>{children}</h2>,
}));

jest.mock('../../components/ui/button', () => ({
  Button: ({ onClick, children, disabled, variant, size }: any) => (
    <button onClick={onClick} disabled={disabled} data-variant={variant} data-size={size}>{children}</button>
  ),
}));

jest.mock('../../components/ui/tabs', () => ({
  Tabs: ({ children, defaultValue, value, onValueChange }: any) => {
    const [currentValue, setCurrentValue] = React.useState(value || defaultValue || 'rules');
    
    React.useEffect(() => {
      if (value !== undefined) {
        setCurrentValue(value);
      }
    }, [value]);
    
    const childrenWithProps = React.Children.map(children, child => {
      if (React.isValidElement(child)) {
        return React.cloneElement(child, {
          currentValue,
          onValueChange: (newValue: string) => {
            setCurrentValue(newValue);
            onValueChange?.(newValue);
          }
        });
      }
      return child;
    });
    
    return <div data-testid="tabs" data-value={currentValue}>{childrenWithProps}</div>;
  },
  TabsContent: ({ children, value, currentValue }: any) => {
    const isVisible = currentValue === value;
    return isVisible ? <div data-testid={`tab-content-${value}`}>{children}</div> : null;
  },
  TabsList: ({ children, className }: any) => <div className={className}>{children}</div>,
  TabsTrigger: ({ children, value, onClick, onValueChange, currentValue }: any) => (
    <button 
      onClick={() => onValueChange?.(value)} 
      data-value={value}
      data-current={currentValue === value}
    >
      {children}
    </button>
  ),
}));

jest.mock('../../components/ui/textarea', () => ({
  Textarea: ({ placeholder, value, onChange, className, rows }: any) => (
    <textarea
      placeholder={placeholder}
      value={value}
      onChange={onChange}
      className={className}
      rows={rows}
      data-testid="textarea"
    />
  ),
}));

jest.mock('../../components/ui/alert', () => ({
  Alert: ({ children, className }: any) => <div className={className} data-testid="alert">{children}</div>,
  AlertDescription: ({ children }: any) => <div>{children}</div>,
}));

// Mock lucide-react icons
jest.mock('lucide-react', () => ({
  Info: () => <span>Info Icon</span>,
}));

describe('GlobalContextDialog', () => {
  const mockOnClose = jest.fn();
  const mockOnUpdate = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders nothing when closed', () => {
    render(
      <GlobalContextDialog
        open={false}
        onClose={mockOnClose}
        onUpdate={mockOnUpdate}
        currentContext={{
          rules: [],
          patterns: []
        }}
      />
    );

    expect(screen.queryByTestId('dialog')).not.toBeInTheDocument();
  });

  it('renders dialog with tabs when open', () => {
    render(
      <GlobalContextDialog
        open={true}
        onClose={mockOnClose}
        onUpdate={mockOnUpdate}
        currentContext={{
          rules: [],
          patterns: []
        }}
      />
    );

    expect(screen.getByTestId('dialog')).toBeInTheDocument();
    expect(screen.getByText('Edit Global Context')).toBeInTheDocument();
    expect(screen.getByText('Rules')).toBeInTheDocument();
    expect(screen.getByText('Patterns')).toBeInTheDocument();
  });

  it('displays current context data in tabs', async () => {
    const testContext = {
      rules: ['Rule 1', 'Rule 2'],
      patterns: ['Pattern A', 'Pattern B']
    };

    render(
      <GlobalContextDialog
        open={true}
        onClose={mockOnClose}
        onUpdate={mockOnUpdate}
        currentContext={testContext}
      />
    );

    // Rules tab should be active by default
    const rulesContent = screen.getByTestId('tab-content-rules');
    expect(rulesContent).toBeInTheDocument();
    
    // Check rules content
    const textareas = screen.getAllByTestId('textarea');
    expect(textareas[0]).toHaveValue('Rule 1\nRule 2');
    
    // Switch to patterns tab
    const patternsTab = screen.getByText('Patterns');
    fireEvent.click(patternsTab);
    
    // Wait for tab switch
    await waitFor(() => {
      expect(screen.getByTestId('tab-content-patterns')).toBeInTheDocument();
    });
    
    // Check patterns content
    const patternsTextarea = screen.getAllByTestId('textarea')[1];
    expect(patternsTextarea).toHaveValue('Pattern A\nPattern B');
  });

  it('updates input values when typing', async () => {
    render(
      <GlobalContextDialog
        open={true}
        onClose={mockOnClose}
        onUpdate={mockOnUpdate}
        currentContext={{
          rules: [],
          patterns: []
        }}
      />
    );

    // Update rules in the first tab
    const rulesTextarea = screen.getAllByTestId('textarea')[0];
    fireEvent.change(rulesTextarea, { target: { value: 'New Rule' } });
    expect(rulesTextarea).toHaveValue('New Rule');
    
    // Switch to patterns tab
    const patternsTab = screen.getByText('Patterns');
    fireEvent.click(patternsTab);
    
    await waitFor(() => {
      expect(screen.getByTestId('tab-content-patterns')).toBeInTheDocument();
    });
    
    // Update patterns
    const patternsTextarea = screen.getAllByTestId('textarea')[1];
    fireEvent.change(patternsTextarea, { target: { value: 'New Pattern' } });
    expect(patternsTextarea).toHaveValue('New Pattern');
  });

  it('calls API and callbacks on save', async () => {
    const mockApiResponse = { success: true };
    (api.updateGlobalContext as jest.Mock).mockResolvedValue(mockApiResponse);

    render(
      <GlobalContextDialog
        open={true}
        onClose={mockOnClose}
        onUpdate={mockOnUpdate}
        currentContext={{
          rules: [],
          patterns: []
        }}
      />
    );

    // Update rules in first tab
    const rulesTextarea = screen.getAllByTestId('textarea')[0];
    fireEvent.change(rulesTextarea, { target: { value: 'Rule 1\nRule 2' } });
    
    // Switch to patterns tab and update
    const patternsTab = screen.getByText('Patterns');
    fireEvent.click(patternsTab);
    
    await waitFor(() => {
      expect(screen.getByTestId('tab-content-patterns')).toBeInTheDocument();
    });
    
    const patternsTextarea = screen.getAllByTestId('textarea')[1];
    fireEvent.change(patternsTextarea, { target: { value: 'Pattern A\nPattern B' } });

    const saveButton = screen.getByText('Save Changes');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(api.updateGlobalContext).toHaveBeenCalledWith({
        rules: ['Rule 1', 'Rule 2'],
        patterns: ['Pattern A', 'Pattern B']
      });
      expect(mockOnUpdate).toHaveBeenCalledWith({
        rules: ['Rule 1', 'Rule 2'],
        patterns: ['Pattern A', 'Pattern B']
      });
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  it('shows loading state while saving', async () => {
    (api.updateGlobalContext as jest.Mock).mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 100))
    );

    render(
      <GlobalContextDialog
        open={true}
        onClose={mockOnClose}
        onUpdate={mockOnUpdate}
        currentContext={{
          rules: [],
          patterns: []
        }}
      />
    );

    const saveButton = screen.getByText('Save Changes');
    fireEvent.click(saveButton);

    expect(saveButton).toBeDisabled();
    expect(screen.getByText('Saving...')).toBeInTheDocument();
  });

  it('handles API errors gracefully', async () => {
    const errorMessage = 'Failed to update context';
    (api.updateGlobalContext as jest.Mock).mockRejectedValue(new Error(errorMessage));

    render(
      <GlobalContextDialog
        open={true}
        onClose={mockOnClose}
        onUpdate={mockOnUpdate}
        currentContext={{
          rules: [],
          patterns: []
        }}
      />
    );

    const saveButton = screen.getByText('Save Changes');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByTestId('alert')).toBeInTheDocument();
      expect(screen.getByText(`Failed to update: ${errorMessage}`)).toBeInTheDocument();
    });

    expect(mockOnUpdate).not.toHaveBeenCalled();
    expect(mockOnClose).not.toHaveBeenCalled();
  });

  it('calls onClose when Cancel button is clicked', () => {
    render(
      <GlobalContextDialog
        open={true}
        onClose={mockOnClose}
        onUpdate={mockOnUpdate}
        currentContext={{
          rules: [],
          patterns: []
        }}
      />
    );

    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('shows markdown editing help text', () => {
    render(
      <GlobalContextDialog
        open={true}
        onClose={mockOnClose}
        onUpdate={mockOnUpdate}
        currentContext={{
          rules: [],
          patterns: []
        }}
      />
    );

    expect(screen.getByText(/You can use markdown formatting/)).toBeInTheDocument();
  });

  it('filters empty lines when saving', async () => {
    (api.updateGlobalContext as jest.Mock).mockResolvedValue({ success: true });

    render(
      <GlobalContextDialog
        open={true}
        onClose={mockOnClose}
        onUpdate={mockOnUpdate}
        currentContext={{
          rules: [],
          patterns: []
        }}
      />
    );

    // Add rules with empty lines
    const rulesTextarea = screen.getAllByTestId('textarea')[0];
    fireEvent.change(rulesTextarea, { target: { value: 'Rule 1\n\n\nRule 2\n\n' } });

    const saveButton = screen.getByText('Save Changes');
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(api.updateGlobalContext).toHaveBeenCalledWith({
        rules: ['Rule 1', 'Rule 2'],
        patterns: []
      });
    });
  });

  it('maintains tab state during updates', async () => {
    render(
      <GlobalContextDialog
        open={true}
        onClose={mockOnClose}
        onUpdate={mockOnUpdate}
        currentContext={{
          rules: ['Rule 1'],
          patterns: ['Pattern 1']
        }}
      />
    );

    // Switch to patterns tab
    const patternsTab = screen.getByText('Patterns');
    fireEvent.click(patternsTab);

    await waitFor(() => {
      expect(screen.getByTestId('tab-content-patterns')).toBeInTheDocument();
    });

    // Update patterns
    const patternsTextarea = screen.getAllByTestId('textarea')[1];
    fireEvent.change(patternsTextarea, { target: { value: 'Updated Pattern' } });

    // Verify we're still on patterns tab
    expect(screen.getByTestId('tab-content-patterns')).toBeInTheDocument();
    expect(screen.queryByTestId('tab-content-rules')).not.toBeInTheDocument();
  });
});