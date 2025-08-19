import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import '@testing-library/jest-dom';
import TokenManagement from '../../pages/TokenManagement';
import * as tokenService from '../../services/tokenService';
import { format } from 'date-fns';
import { ThemeProvider } from '../../contexts/ThemeContext';

// Mock dependencies
jest.mock('../../services/tokenService');
jest.mock('date-fns', () => ({
  format: jest.fn((date) => 'formatted-date'),
}));

const mockTokenService = jest.mocked(tokenService);

const mockTokens: tokenService.Token[] = [
  {
    id: '1',
    name: 'Test Token 1',
    description: 'Test description 1',
    is_active: true,
    rate_limit: 100,
    created_at: '2024-01-01T00:00:00Z',
    last_used_at: '2024-01-02T00:00:00Z',
  },
  {
    id: '2',
    name: 'Test Token 2',
    description: 'Test description 2',
    is_active: false,
    rate_limit: 50,
    created_at: '2024-01-03T00:00:00Z',
    last_used_at: null,
  },
];

const renderWithTheme = (component: React.ReactElement) => {
  return render(
    <ThemeProvider>
      {component}
    </ThemeProvider>
  );
};

describe('TokenManagement', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockTokenService.listTokens.mockResolvedValue(mockTokens);
  });

  describe('Scope removal - admin scope', () => {
    it('should not include admin scope in available scopes', () => {
      renderWithTheme(<TokenManagement />);
      
      // Open new token dialog
      const newTokenButton = screen.getByRole('button', { name: /new token/i });
      fireEvent.click(newTokenButton);
      
      // Check that admin scope is not in the list
      const scopeCheckboxes = screen.getAllByRole('checkbox');
      const scopeLabels = scopeCheckboxes.map(checkbox => {
        const label = checkbox.closest('label');
        return label?.textContent || '';
      });
      
      expect(scopeLabels).not.toContain('Admin');
      expect(scopeLabels).toContain('Read Tasks');
      expect(scopeLabels).toContain('Write Tasks');
      expect(scopeLabels).toContain('Read Context');
      expect(scopeLabels).toContain('Write Context');
      expect(scopeLabels).toContain('Read Agents');
      expect(scopeLabels).toContain('Write Agents');
      expect(scopeLabels).toContain('Execute MCP');
    });

    it('should only have 7 available scopes after admin removal', () => {
      renderWithTheme(<TokenManagement />);
      
      // Open new token dialog
      const newTokenButton = screen.getByRole('button', { name: /new token/i });
      fireEvent.click(newTokenButton);
      
      // Count scope checkboxes
      const scopeCheckboxes = screen.getAllByRole('checkbox');
      // Filter out any non-scope checkboxes
      const scopeLabels = scopeCheckboxes.filter(checkbox => {
        const label = checkbox.closest('label');
        const labelText = label?.textContent || '';
        return labelText.includes('Read') || labelText.includes('Write') || labelText.includes('Execute');
      });
      
      expect(scopeLabels).toHaveLength(7);
    });
  });

  it('renders the page title and description', () => {
    renderWithTheme(<TokenManagement />);
    
    expect(screen.getByText('API Token Management')).toBeInTheDocument();
    expect(screen.getByText(/manage your api tokens/i)).toBeInTheDocument();
  });

  it('loads and displays tokens on mount', async () => {
    renderWithTheme(<TokenManagement />);
    
    await waitFor(() => {
      expect(mockTokenService.listTokens).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(screen.getByText('Test Token 1')).toBeInTheDocument();
      expect(screen.getByText('Test Token 2')).toBeInTheDocument();
    });
  });

  it('shows loading state while fetching tokens', async () => {
    mockTokenService.listTokens.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));
    
    renderWithTheme(<TokenManagement />);
    
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('opens create dialog when Create New Token button is clicked', async () => {
    renderWithTheme(<TokenManagement />);
    
    const createButton = screen.getByRole('button', { name: /create new token/i });
    fireEvent.click(createButton);

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /create new api token/i })).toBeInTheDocument();
    });
  });

  it('creates a new token with form data', async () => {
    const newToken = {
      id: '3',
      name: 'New Token',
      description: 'New token description',
      token: 'generated-token-value',
      is_active: true,
      rate_limit: 200,
      created_at: '2024-01-04T00:00:00Z',
      last_used_at: null,
    };
    
    mockTokenService.createToken.mockResolvedValue(newToken);
    mockTokenService.listTokens.mockResolvedValueOnce(mockTokens).mockResolvedValueOnce([...mockTokens, newToken]);
    
    renderWithTheme(<TokenManagement />);
    
    // Open create dialog
    const createButton = screen.getByRole('button', { name: /create new token/i });
    fireEvent.click(createButton);

    // Fill form
    const nameInput = screen.getByLabelText(/token name/i);
    const descriptionInput = screen.getByLabelText(/description/i);
    const rateLimitInput = screen.getByLabelText(/rate limit/i);
    
    fireEvent.change(nameInput, { target: { value: 'New Token' } });
    fireEvent.change(descriptionInput, { target: { value: 'New token description' } });
    fireEvent.change(rateLimitInput, { target: { value: '200' } });

    // Submit form
    const submitButton = screen.getByRole('button', { name: /create/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockTokenService.createToken).toHaveBeenCalledWith({
        name: 'New Token',
        description: 'New token description',
        rate_limit: 200,
      });
    });

    // Check if token display dialog is shown
    await waitFor(() => {
      expect(screen.getByText(/token created successfully/i)).toBeInTheDocument();
      expect(screen.getByText('generated-token-value')).toBeInTheDocument();
    });
  });

  it('copies token to clipboard when copy button is clicked', async () => {
    const mockClipboard = {
      writeText: jest.fn().mockResolvedValue(undefined),
    };
    Object.assign(navigator, { clipboard: mockClipboard });

    const newToken = {
      id: '3',
      name: 'New Token',
      token: 'test-token-to-copy',
      is_active: true,
      rate_limit: 100,
      created_at: '2024-01-04T00:00:00Z',
    };
    
    mockTokenService.createToken.mockResolvedValue(newToken);
    
    renderWithTheme(<TokenManagement />);
    
    // Create a token
    const createButton = screen.getByRole('button', { name: /create new token/i });
    fireEvent.click(createButton);
    
    const nameInput = screen.getByLabelText(/token name/i);
    fireEvent.change(nameInput, { target: { value: 'New Token' } });
    
    const submitButton = screen.getByRole('button', { name: /create/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('test-token-to-copy')).toBeInTheDocument();
    });

    // Click copy button
    const copyButton = screen.getByRole('button', { name: /copy to clipboard/i });
    fireEvent.click(copyButton);

    expect(mockClipboard.writeText).toHaveBeenCalledWith('test-token-to-copy');
    
    await waitFor(() => {
      expect(screen.getByText(/copied!/i)).toBeInTheDocument();
    });
  });

  it('toggles token activation status', async () => {
    mockTokenService.updateToken.mockResolvedValue({ ...mockTokens[0], is_active: false });
    
    renderWithTheme(<TokenManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Token 1')).toBeInTheDocument();
    });

    // Find the first token's row
    const firstTokenRow = screen.getByText('Test Token 1').closest('tr')!;
    const toggleSwitch = within(firstTokenRow).getByRole('checkbox');
    
    fireEvent.click(toggleSwitch);

    await waitFor(() => {
      expect(mockTokenService.updateToken).toHaveBeenCalledWith('1', { is_active: false });
    });
  });

  it('deletes a token when delete button is clicked and confirmed', async () => {
    mockTokenService.deleteToken.mockResolvedValue(undefined);
    mockTokenService.listTokens.mockResolvedValueOnce(mockTokens).mockResolvedValueOnce([mockTokens[1]]);
    
    renderWithTheme(<TokenManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Token 1')).toBeInTheDocument();
    });

    // Find delete button for first token
    const firstTokenRow = screen.getByText('Test Token 1').closest('tr')!;
    const deleteButton = within(firstTokenRow).getByRole('button', { name: /delete/i });
    
    fireEvent.click(deleteButton);

    // Confirm deletion
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /confirm deletion/i })).toBeInTheDocument();
    });
    
    const confirmButton = screen.getByRole('button', { name: /delete/i });
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(mockTokenService.deleteToken).toHaveBeenCalledWith('1');
    });

    // Check if tokens are refreshed
    await waitFor(() => {
      expect(mockTokenService.listTokens).toHaveBeenCalledTimes(2);
    });
  });

  it('cancels token deletion when cancel is clicked', async () => {
    renderWithTheme(<TokenManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Token 1')).toBeInTheDocument();
    });

    // Find delete button for first token
    const firstTokenRow = screen.getByText('Test Token 1').closest('tr')!;
    const deleteButton = within(firstTokenRow).getByRole('button', { name: /delete/i });
    
    fireEvent.click(deleteButton);

    // Cancel deletion
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /confirm deletion/i })).toBeInTheDocument();
    });
    
    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    fireEvent.click(cancelButton);

    await waitFor(() => {
      expect(screen.queryByRole('heading', { name: /confirm deletion/i })).not.toBeInTheDocument();
    });

    expect(mockTokenService.deleteToken).not.toHaveBeenCalled();
  });

  it('displays error message when token creation fails', async () => {
    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
    mockTokenService.createToken.mockRejectedValue(new Error('Creation failed'));
    
    renderWithTheme(<TokenManagement />);
    
    // Open create dialog
    const createButton = screen.getByRole('button', { name: /create new token/i });
    fireEvent.click(createButton);

    // Fill and submit form
    const nameInput = screen.getByLabelText(/token name/i);
    fireEvent.change(nameInput, { target: { value: 'New Token' } });
    
    const submitButton = screen.getByRole('button', { name: /create/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalledWith('Failed to create token:', expect.any(Error));
    });

    consoleErrorSpy.mockRestore();
  });

  it('displays error message when loading tokens fails', async () => {
    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
    mockTokenService.listTokens.mockRejectedValue(new Error('Load failed'));
    
    renderWithTheme(<TokenManagement />);

    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalledWith('Failed to load tokens:', expect.any(Error));
    });

    consoleErrorSpy.mockRestore();
  });

  it('formats dates correctly', async () => {
    renderWithTheme(<TokenManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Token 1')).toBeInTheDocument();
    });

    // Check if date formatting function was called
    expect(format).toHaveBeenCalled();
  });

  it('displays Never for tokens that have never been used', async () => {
    renderWithTheme(<TokenManagement />);
    
    await waitFor(() => {
      expect(screen.getByText('Test Token 2')).toBeInTheDocument();
    });

    // Find the second token's row which has null last_used_at
    const secondTokenRow = screen.getByText('Test Token 2').closest('tr')!;
    expect(within(secondTokenRow).getByText('Never')).toBeInTheDocument();
  });

  it('validates form fields before submission', async () => {
    renderWithTheme(<TokenManagement />);
    
    // Open create dialog
    const createButton = screen.getByRole('button', { name: /create new token/i });
    fireEvent.click(createButton);

    // Try to submit empty form
    const submitButton = screen.getByRole('button', { name: /create/i });
    fireEvent.click(submitButton);

    // Check that the API was not called
    expect(mockTokenService.createToken).not.toHaveBeenCalled();

    // Fill only name and try again
    const nameInput = screen.getByLabelText(/token name/i);
    fireEvent.change(nameInput, { target: { value: 'Test' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockTokenService.createToken).toHaveBeenCalledWith({
        name: 'Test',
        description: '',
        rate_limit: 100, // default value
      });
    });
  });
});