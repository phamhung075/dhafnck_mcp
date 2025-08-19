import * as tokenService from '../../services/tokenService';
import { useAuthenticatedFetch } from '../../hooks/useAuthenticatedFetch';

// Mock the authenticated fetch hook
jest.mock('../../hooks/useAuthenticatedFetch', () => ({
  useAuthenticatedFetch: jest.fn(),
}));

const mockUseAuthenticatedFetch = jest.mocked(useAuthenticatedFetch);

describe('tokenService', () => {
  let mockFetch: jest.Mock;
  const baseUrl = '/api/v2/tokens';

  beforeEach(() => {
    jest.clearAllMocks();
    mockFetch = jest.fn();
    mockUseAuthenticatedFetch.mockReturnValue(mockFetch);
  });

  describe('listTokens', () => {
    it('fetches all tokens successfully', async () => {
      const mockTokens = [
        { id: '1', name: 'Token 1' },
        { id: '2', name: 'Token 2' },
      ];
      
      mockFetch.mockResolvedValue(mockTokens);

      const result = await tokenService.listTokens();

      expect(mockFetch).toHaveBeenCalledWith(baseUrl, {
        method: 'GET',
      });
      expect(result).toEqual(mockTokens);
    });

    it('handles empty token list', async () => {
      mockFetch.mockResolvedValue([]);

      const result = await tokenService.listTokens();

      expect(result).toEqual([]);
    });

    it('handles fetch error', async () => {
      const error = new Error('Network error');
      mockFetch.mockRejectedValue(error);

      await expect(tokenService.listTokens()).rejects.toThrow('Network error');
    });
  });

  describe('getToken', () => {
    it('fetches a specific token by id', async () => {
      const mockToken = { id: '123', name: 'Test Token' };
      mockFetch.mockResolvedValue(mockToken);

      const result = await tokenService.getToken('123');

      expect(mockFetch).toHaveBeenCalledWith(`${baseUrl}/123`, {
        method: 'GET',
      });
      expect(result).toEqual(mockToken);
    });

    it('handles not found error', async () => {
      mockFetch.mockRejectedValue(new Error('Token not found'));

      await expect(tokenService.getToken('999')).rejects.toThrow('Token not found');
    });
  });

  describe('createToken', () => {
    it('creates a new token with all fields', async () => {
      const newTokenData = {
        name: 'New Token',
        description: 'Test description',
        rate_limit: 100,
      };
      
      const createdToken = {
        ...newTokenData,
        id: '456',
        token: 'generated-token-value',
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
      };
      
      mockFetch.mockResolvedValue(createdToken);

      const result = await tokenService.createToken(newTokenData);

      expect(mockFetch).toHaveBeenCalledWith(baseUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newTokenData),
      });
      expect(result).toEqual(createdToken);
    });

    it('creates a token with minimal fields', async () => {
      const minimalData = { name: 'Minimal Token' };
      const createdToken = {
        ...minimalData,
        id: '789',
        token: 'minimal-token',
        is_active: true,
      };
      
      mockFetch.mockResolvedValue(createdToken);

      const result = await tokenService.createToken(minimalData);

      expect(mockFetch).toHaveBeenCalledWith(baseUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(minimalData),
      });
      expect(result).toEqual(createdToken);
    });

    it('handles validation error', async () => {
      mockFetch.mockRejectedValue(new Error('Validation failed'));

      await expect(tokenService.createToken({ name: '' })).rejects.toThrow('Validation failed');
    });
  });

  describe('updateToken', () => {
    it('updates token fields', async () => {
      const updates = {
        description: 'Updated description',
        is_active: false,
        rate_limit: 200,
      };
      
      const updatedToken = {
        id: '123',
        name: 'Test Token',
        ...updates,
      };
      
      mockFetch.mockResolvedValue(updatedToken);

      const result = await tokenService.updateToken('123', updates);

      expect(mockFetch).toHaveBeenCalledWith(`${baseUrl}/123`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates),
      });
      expect(result).toEqual(updatedToken);
    });

    it('updates only is_active field', async () => {
      const updates = { is_active: true };
      const updatedToken = { id: '123', name: 'Token', is_active: true };
      
      mockFetch.mockResolvedValue(updatedToken);

      const result = await tokenService.updateToken('123', updates);

      expect(mockFetch).toHaveBeenCalledWith(`${baseUrl}/123`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updates),
      });
      expect(result.is_active).toBe(true);
    });
  });

  describe('deleteToken', () => {
    it('deletes a token successfully', async () => {
      mockFetch.mockResolvedValue({ success: true });

      await tokenService.deleteToken('123');

      expect(mockFetch).toHaveBeenCalledWith(`${baseUrl}/123`, {
        method: 'DELETE',
      });
    });

    it('handles deletion error', async () => {
      mockFetch.mockRejectedValue(new Error('Deletion failed'));

      await expect(tokenService.deleteToken('123')).rejects.toThrow('Deletion failed');
    });
  });

  describe('regenerateToken', () => {
    it('regenerates a token and returns new value', async () => {
      const regeneratedToken = {
        id: '123',
        name: 'Test Token',
        token: 'new-regenerated-token',
        is_active: true,
      };
      
      mockFetch.mockResolvedValue(regeneratedToken);

      const result = await tokenService.regenerateToken('123');

      expect(mockFetch).toHaveBeenCalledWith(`${baseUrl}/123/regenerate`, {
        method: 'POST',
      });
      expect(result).toEqual(regeneratedToken);
      expect(result.token).toBe('new-regenerated-token');
    });

    it('handles regeneration error', async () => {
      mockFetch.mockRejectedValue(new Error('Regeneration failed'));

      await expect(tokenService.regenerateToken('123')).rejects.toThrow('Regeneration failed');
    });
  });

  describe('validateToken', () => {
    it('validates a token successfully', async () => {
      const validationResult = {
        valid: true,
        user_id: 'user-123',
        token_id: 'token-123',
      };
      
      mockFetch.mockResolvedValue(validationResult);

      const result = await tokenService.validateToken('test-token-value');

      expect(mockFetch).toHaveBeenCalledWith(`${baseUrl}/validate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token: 'test-token-value' }),
      });
      expect(result).toEqual(validationResult);
    });

    it('handles invalid token', async () => {
      const invalidResult = {
        valid: false,
        error: 'Invalid token',
      };
      
      mockFetch.mockResolvedValue(invalidResult);

      const result = await tokenService.validateToken('invalid-token');

      expect(result.valid).toBe(false);
      expect(result.error).toBe('Invalid token');
    });
  });

  describe('getTokenStats', () => {
    it('fetches token statistics', async () => {
      const stats = {
        total_requests: 1000,
        requests_today: 50,
        rate_limit_hits: 5,
        last_used: '2024-01-01T12:00:00Z',
      };
      
      mockFetch.mockResolvedValue(stats);

      const result = await tokenService.getTokenStats('123');

      expect(mockFetch).toHaveBeenCalledWith(`${baseUrl}/123/stats`, {
        method: 'GET',
      });
      expect(result).toEqual(stats);
    });

    it('handles stats not available', async () => {
      mockFetch.mockResolvedValue(null);

      const result = await tokenService.getTokenStats('123');

      expect(result).toBeNull();
    });
  });

  describe('error handling', () => {
    it('handles network timeout', async () => {
      const timeoutError = new Error('Request timeout');
      timeoutError.name = 'TimeoutError';
      mockFetch.mockRejectedValue(timeoutError);

      await expect(tokenService.listTokens()).rejects.toThrow('Request timeout');
    });

    it('handles 401 unauthorized', async () => {
      const authError = new Error('Unauthorized');
      mockFetch.mockRejectedValue(authError);

      await expect(tokenService.listTokens()).rejects.toThrow('Unauthorized');
    });

    it('handles 403 forbidden', async () => {
      const forbiddenError = new Error('Forbidden');
      mockFetch.mockRejectedValue(forbiddenError);

      await expect(tokenService.createToken({ name: 'Test' })).rejects.toThrow('Forbidden');
    });

    it('handles 500 server error', async () => {
      const serverError = new Error('Internal Server Error');
      mockFetch.mockRejectedValue(serverError);

      await expect(tokenService.listTokens()).rejects.toThrow('Internal Server Error');
    });
  });

  describe('edge cases', () => {
    it('handles empty token name', async () => {
      const emptyNameToken = { name: '' };
      mockFetch.mockRejectedValue(new Error('Name is required'));

      await expect(tokenService.createToken(emptyNameToken)).rejects.toThrow('Name is required');
    });

    it('handles very long token names', async () => {
      const longName = 'a'.repeat(256);
      const tokenData = { name: longName };
      const createdToken = { id: '123', name: longName };
      
      mockFetch.mockResolvedValue(createdToken);

      const result = await tokenService.createToken(tokenData);

      expect(result.name).toBe(longName);
    });

    it('handles special characters in token names', async () => {
      const specialName = 'Test!@#$%^&*()';
      const tokenData = { name: specialName };
      const createdToken = { id: '123', name: specialName };
      
      mockFetch.mockResolvedValue(createdToken);

      const result = await tokenService.createToken(tokenData);

      expect(result.name).toBe(specialName);
    });

    it('handles negative rate limits', async () => {
      const invalidData = { name: 'Test', rate_limit: -1 };
      mockFetch.mockRejectedValue(new Error('Rate limit must be positive'));

      await expect(tokenService.createToken(invalidData)).rejects.toThrow('Rate limit must be positive');
    });

    it('handles very large rate limits', async () => {
      const largeRateLimit = 1000000;
      const tokenData = { name: 'Test', rate_limit: largeRateLimit };
      const createdToken = { id: '123', ...tokenData };
      
      mockFetch.mockResolvedValue(createdToken);

      const result = await tokenService.createToken(tokenData);

      expect(result.rate_limit).toBe(largeRateLimit);
    });
  });
});