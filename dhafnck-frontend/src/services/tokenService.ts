import { authenticatedFetch } from '../hooks/useAuthenticatedFetch';

interface GenerateTokenRequest {
  name: string;
  scopes: string[];
  expires_in_days: number;
  rate_limit?: number;
}

interface TokenResponse {
  id: string;
  name: string;
  token?: string;
  scopes: string[];
  created_at: string;
  expires_at: string;
  last_used_at?: string;
  usage_count: number;
  rate_limit?: number;
  is_active: boolean;
}

interface TokenListResponse {
  data: TokenResponse[];
  total: number;
}

class TokenService {
  private baseUrl = '/api/v2/tokens';

  async generateToken(request: GenerateTokenRequest): Promise<{ data: TokenResponse }> {
    const response = await authenticatedFetch(this.baseUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Failed to generate token' }));
      throw new Error(error.message || 'Failed to generate token');
    }

    return response.json();
  }

  async listTokens(): Promise<TokenListResponse> {
    const response = await authenticatedFetch(this.baseUrl, {
      method: 'GET',
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Failed to fetch tokens' }));
      throw new Error(error.message || 'Failed to fetch tokens');
    }

    return response.json();
  }

  async revokeToken(tokenId: string): Promise<void> {
    const response = await authenticatedFetch(`${this.baseUrl}/${tokenId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Failed to revoke token' }));
      throw new Error(error.message || 'Failed to revoke token');
    }
  }

  async getTokenDetails(tokenId: string): Promise<TokenResponse> {
    const response = await authenticatedFetch(`${this.baseUrl}/${tokenId}`, {
      method: 'GET',
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Failed to fetch token details' }));
      throw new Error(error.message || 'Failed to fetch token details');
    }

    return response.json();
  }

  async updateTokenScopes(tokenId: string, scopes: string[]): Promise<TokenResponse> {
    const response = await authenticatedFetch(`${this.baseUrl}/${tokenId}/scopes`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ scopes }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Failed to update token scopes' }));
      throw new Error(error.message || 'Failed to update token scopes');
    }

    return response.json();
  }

  async rotateToken(tokenId: string): Promise<{ data: TokenResponse }> {
    const response = await authenticatedFetch(`${this.baseUrl}/${tokenId}/rotate`, {
      method: 'POST',
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Failed to rotate token' }));
      throw new Error(error.message || 'Failed to rotate token');
    }

    return response.json();
  }

  async getTokenUsageStats(tokenId: string): Promise<any> {
    const response = await authenticatedFetch(`${this.baseUrl}/${tokenId}/usage`, {
      method: 'GET',
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Failed to fetch usage stats' }));
      throw new Error(error.message || 'Failed to fetch usage stats');
    }

    return response.json();
  }

  // Validate a token (useful for testing)
  async validateToken(token: string): Promise<{ valid: boolean; scopes?: string[]; user_id?: string }> {
    const response = await fetch('/api/v2/tokens/validate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      return { valid: false };
    }

    return response.json();
  }
}

export const tokenService = new TokenService();