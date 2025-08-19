import pytest
import os
import json
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path

from fastmcp.server.auth.mcp_auth_config import (
    find_mcp_config_file,
    load_mcp_config,
    extract_jwt_secret,
    is_bearer_token_auth,
    get_mcp_server_name,
    DEFAULT_CONFIG_PATHS,
)


class TestFindMcpConfigFile:
    """Test cases for find_mcp_config_file function."""

    def test_find_config_in_default_paths(self):
        """Test finding config file in default paths."""
        with patch('pathlib.Path.exists') as mock_exists:
            # Mock that the second default path exists
            mock_exists.side_effect = [False, True, False]
            
            result = find_mcp_config_file()
            
            assert result == Path(DEFAULT_CONFIG_PATHS[1])
            assert mock_exists.call_count == 2

    def test_find_config_with_custom_paths(self):
        """Test finding config file with custom paths."""
        custom_paths = ["/custom/path1.json", "/custom/path2.json"]
        
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.side_effect = [False, True]
            
            result = find_mcp_config_file(custom_paths)
            
            assert result == Path(custom_paths[1])
            assert mock_exists.call_count == 2

    def test_no_config_file_found(self):
        """Test when no config file is found."""
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = False
            
            result = find_mcp_config_file()
            
            assert result is None
            assert mock_exists.call_count == len(DEFAULT_CONFIG_PATHS)

    def test_empty_paths_list(self):
        """Test with empty paths list."""
        result = find_mcp_config_file([])
        assert result is None


class TestLoadMcpConfig:
    """Test cases for load_mcp_config function."""

    def test_load_valid_config(self):
        """Test loading a valid configuration file."""
        config_data = {
            "mcp": {
                "servers": {
                    "dhafnck-mcp": {
                        "env": {
                            "JWT_SECRET": "test-secret"
                        }
                    }
                }
            }
        }
        
        mock_file_content = json.dumps(config_data)
        
        with patch('builtins.open', mock_open(read_data=mock_file_content)):
            result = load_mcp_config("/path/to/config.json")
            
            assert result == config_data

    def test_load_config_file_not_found(self):
        """Test loading config when file doesn't exist."""
        with patch('builtins.open', side_effect=FileNotFoundError()):
            result = load_mcp_config("/nonexistent/config.json")
            
            assert result is None

    def test_load_config_invalid_json(self):
        """Test loading config with invalid JSON."""
        invalid_json = "{ invalid json content"
        
        with patch('builtins.open', mock_open(read_data=invalid_json)):
            result = load_mcp_config("/path/to/config.json")
            
            assert result is None

    def test_load_config_permission_error(self):
        """Test loading config with permission error."""
        with patch('builtins.open', side_effect=PermissionError()):
            result = load_mcp_config("/path/to/config.json")
            
            assert result is None

    def test_load_config_path_object(self):
        """Test loading config with Path object."""
        config_data = {"test": "data"}
        mock_file_content = json.dumps(config_data)
        
        with patch('builtins.open', mock_open(read_data=mock_file_content)):
            result = load_mcp_config(Path("/path/to/config.json"))
            
            assert result == config_data


class TestExtractJwtSecret:
    """Test cases for extract_jwt_secret function."""

    def test_extract_jwt_secret_from_env(self):
        """Test extracting JWT secret from env configuration."""
        config = {
            "mcp": {
                "servers": {
                    "dhafnck-mcp": {
                        "env": {
                            "JWT_SECRET": "my-secret-key"
                        }
                    }
                }
            }
        }
        
        result = extract_jwt_secret(config, "dhafnck-mcp")
        assert result == "my-secret-key"

    def test_extract_jwt_secret_server_not_found(self):
        """Test extracting JWT secret when server doesn't exist."""
        config = {
            "mcp": {
                "servers": {
                    "other-server": {}
                }
            }
        }
        
        result = extract_jwt_secret(config, "dhafnck-mcp")
        assert result is None

    def test_extract_jwt_secret_no_env(self):
        """Test extracting JWT secret when env is missing."""
        config = {
            "mcp": {
                "servers": {
                    "dhafnck-mcp": {
                        "command": "python"
                    }
                }
            }
        }
        
        result = extract_jwt_secret(config, "dhafnck-mcp")
        assert result is None

    def test_extract_jwt_secret_no_jwt_secret(self):
        """Test extracting JWT secret when JWT_SECRET is missing."""
        config = {
            "mcp": {
                "servers": {
                    "dhafnck-mcp": {
                        "env": {
                            "OTHER_VAR": "value"
                        }
                    }
                }
            }
        }
        
        result = extract_jwt_secret(config, "dhafnck-mcp")
        assert result is None

    def test_extract_jwt_secret_empty_config(self):
        """Test extracting JWT secret from empty config."""
        result = extract_jwt_secret({}, "dhafnck-mcp")
        assert result is None

    def test_extract_jwt_secret_malformed_config(self):
        """Test extracting JWT secret from malformed config."""
        config = {"mcp": "not a dict"}
        result = extract_jwt_secret(config, "dhafnck-mcp")
        assert result is None


class TestIsBearerTokenAuth:
    """Test cases for is_bearer_token_auth function."""

    def test_bearer_token_auth_detected(self):
        """Test detecting Bearer token authentication."""
        config = {
            "mcp": {
                "servers": {
                    "dhafnck-mcp": {
                        "env": {
                            "DHAFNCK_MCP_AUTH_TYPE": "bearer_token"
                        }
                    }
                }
            }
        }
        
        result = is_bearer_token_auth(config, "dhafnck-mcp")
        assert result is True

    def test_bearer_token_auth_case_insensitive(self):
        """Test Bearer token auth detection is case-insensitive."""
        config = {
            "mcp": {
                "servers": {
                    "dhafnck-mcp": {
                        "env": {
                            "DHAFNCK_MCP_AUTH_TYPE": "BEARER_TOKEN"
                        }
                    }
                }
            }
        }
        
        result = is_bearer_token_auth(config, "dhafnck-mcp")
        assert result is True

    def test_not_bearer_token_auth(self):
        """Test when auth type is not Bearer token."""
        config = {
            "mcp": {
                "servers": {
                    "dhafnck-mcp": {
                        "env": {
                            "DHAFNCK_MCP_AUTH_TYPE": "oauth2"
                        }
                    }
                }
            }
        }
        
        result = is_bearer_token_auth(config, "dhafnck-mcp")
        assert result is False

    def test_no_auth_type(self):
        """Test when auth type is not specified."""
        config = {
            "mcp": {
                "servers": {
                    "dhafnck-mcp": {
                        "env": {
                            "OTHER_VAR": "value"
                        }
                    }
                }
            }
        }
        
        result = is_bearer_token_auth(config, "dhafnck-mcp")
        assert result is False

    def test_empty_config_bearer_auth(self):
        """Test Bearer auth check with empty config."""
        result = is_bearer_token_auth({}, "dhafnck-mcp")
        assert result is False


class TestGetMcpServerName:
    """Test cases for get_mcp_server_name function."""

    @patch.dict(os.environ, {"MCP_SERVER_NAME": "test-server"}, clear=True)
    def test_get_server_name_from_env(self):
        """Test getting server name from environment variable."""
        result = get_mcp_server_name()
        assert result == "test-server"

    @patch.dict(os.environ, {}, clear=True)
    def test_get_server_name_default(self):
        """Test getting default server name."""
        result = get_mcp_server_name()
        assert result == "dhafnck-mcp"

    @patch.dict(os.environ, {"MCP_SERVER_NAME": ""}, clear=True)
    def test_get_server_name_empty_env(self):
        """Test getting server name with empty env variable."""
        result = get_mcp_server_name()
        assert result == "dhafnck-mcp"

    @patch.dict(os.environ, {"MCP_SERVER_NAME": "  spaces  "}, clear=True)
    def test_get_server_name_with_spaces(self):
        """Test getting server name with spaces."""
        result = get_mcp_server_name()
        assert result == "spaces"


class TestIntegration:
    """Integration tests for MCP auth config functions."""

    def test_full_config_flow(self):
        """Test the full configuration flow."""
        config_data = {
            "mcp": {
                "servers": {
                    "dhafnck-mcp": {
                        "env": {
                            "JWT_SECRET": "integration-secret",
                            "DHAFNCK_MCP_AUTH_TYPE": "bearer_token"
                        }
                    }
                }
            }
        }
        
        mock_file_content = json.dumps(config_data)
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=mock_file_content)):
                # Find config file
                config_path = find_mcp_config_file()
                assert config_path is not None
                
                # Load config
                config = load_mcp_config(config_path)
                assert config is not None
                
                # Extract JWT secret
                secret = extract_jwt_secret(config, "dhafnck-mcp")
                assert secret == "integration-secret"
                
                # Check auth type
                is_bearer = is_bearer_token_auth(config, "dhafnck-mcp")
                assert is_bearer is True

    def test_multiple_servers_config(self):
        """Test configuration with multiple servers."""
        config = {
            "mcp": {
                "servers": {
                    "server1": {
                        "env": {
                            "JWT_SECRET": "secret1",
                            "DHAFNCK_MCP_AUTH_TYPE": "bearer_token"
                        }
                    },
                    "server2": {
                        "env": {
                            "JWT_SECRET": "secret2",
                            "DHAFNCK_MCP_AUTH_TYPE": "oauth2"
                        }
                    },
                    "server3": {
                        "env": {
                            "OTHER_VAR": "value"
                        }
                    }
                }
            }
        }
        
        # Test server1
        assert extract_jwt_secret(config, "server1") == "secret1"
        assert is_bearer_token_auth(config, "server1") is True
        
        # Test server2
        assert extract_jwt_secret(config, "server2") == "secret2"
        assert is_bearer_token_auth(config, "server2") is False
        
        # Test server3
        assert extract_jwt_secret(config, "server3") is None
        assert is_bearer_token_auth(config, "server3") is False
        
        # Test non-existent server
        assert extract_jwt_secret(config, "server4") is None
        assert is_bearer_token_auth(config, "server4") is False


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_unicode_in_config(self):
        """Test handling Unicode characters in config."""
        config = {
            "mcp": {
                "servers": {
                    "dhafnck-mcp": {
                        "env": {
                            "JWT_SECRET": "秘密キー🔐",
                            "DHAFNCK_MCP_AUTH_TYPE": "bearer_token"
                        }
                    }
                }
            }
        }
        
        secret = extract_jwt_secret(config, "dhafnck-mcp")
        assert secret == "秘密キー🔐"

    def test_nested_config_errors(self):
        """Test handling of various nested config errors."""
        test_cases = [
            {"mcp": None},
            {"mcp": {"servers": None}},
            {"mcp": {"servers": {"dhafnck-mcp": None}}},
            {"mcp": {"servers": {"dhafnck-mcp": {"env": None}}}},
        ]
        
        for config in test_cases:
            assert extract_jwt_secret(config, "dhafnck-mcp") is None
            assert is_bearer_token_auth(config, "dhafnck-mcp") is False

    def test_special_characters_in_server_name(self):
        """Test handling special characters in server names."""
        config = {
            "mcp": {
                "servers": {
                    "server-with-dashes": {
                        "env": {"JWT_SECRET": "secret1"}
                    },
                    "server.with.dots": {
                        "env": {"JWT_SECRET": "secret2"}
                    },
                    "server_with_underscores": {
                        "env": {"JWT_SECRET": "secret3"}
                    }
                }
            }
        }
        
        assert extract_jwt_secret(config, "server-with-dashes") == "secret1"
        assert extract_jwt_secret(config, "server.with.dots") == "secret2"
        assert extract_jwt_secret(config, "server_with_underscores") == "secret3"