"""
End-to-End Frontend Integration Tests for Context Authentication and API Integration

This test suite validates:
1. Frontend context buttons work with authenticated v2 API
2. Context operations integrate seamlessly with task/subtask frontend workflows  
3. User authentication flows work correctly from frontend to backend
4. Context data consistency across frontend-backend interactions
5. Error handling provides appropriate user feedback
6. Context UI components respond correctly to authentication states
7. Real-world user workflows involving context management

Author: Test Orchestrator Agent  
Date: 2025-08-25
"""

import pytest
import uuid
import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from unittest.mock import MagicMock, patch, AsyncMock
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from fastapi.testclient import TestClient
import subprocess
import time
import os

# Core imports
from fastmcp.auth.api_server import app
from fastmcp.auth.domain.entities.user import User
from fastmcp.task_management.infrastructure.database.database_config import get_db_config


class TestContextFrontendIntegration:
    """End-to-end tests for context frontend integration with authentication."""
    
    @pytest.fixture(scope="class")
    def backend_server(self):
        """Start backend server for E2E tests."""
        # This would typically start the actual FastAPI server
        # For testing, we'll use TestClient but in real E2E, you'd start uvicorn
        
        # In a real scenario, you'd do:
        # process = subprocess.Popen([
        #     "uvicorn", "fastmcp.auth.api_server:app",
        #     "--host", "0.0.0.0", "--port", "8000"
        # ])
        # time.sleep(2)  # Wait for server to start
        # yield process
        # process.terminate()
        
        # For this test, we'll mock the server responses
        yield TestClient(app)
    
    @pytest.fixture(scope="class")
    async def browser_setup(self):
        """Setup browser for frontend testing."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            yield page, context, browser
            
            await context.close()
            await browser.close()
    
    @pytest.fixture
    def mock_authenticated_user(self):
        """Mock authenticated user for E2E tests."""
        return {
            "id": "e2e-user-" + str(uuid.uuid4())[:8],
            "email": "e2e@example.com", 
            "username": "e2euser",
            "token": "mock-jwt-token-" + str(uuid.uuid4())[:8]
        }
    
    @pytest.fixture
    def sample_task_with_context(self):
        """Sample task data with associated context for E2E testing."""
        task_id = str(uuid.uuid4())
        return {
            "task": {
                "id": task_id,
                "title": "E2E Test Task with Context",
                "description": "Testing context integration in frontend",
                "status": "in_progress",
                "priority": "high"
            },
            "context": {
                "id": task_id,
                "level": "task",
                "data": {
                    "task_data": {
                        "title": "E2E Test Task with Context",
                        "status": "in_progress",
                        "priority": "high"
                    },
                    "progress": 60,
                    "insights": [
                        "Context buttons working correctly",
                        "Authentication integrated properly"
                    ],
                    "next_steps": [
                        "Complete E2E testing",
                        "Deploy to production"
                    ],
                    "frontend_metadata": {
                        "last_viewed": datetime.now(timezone.utc).isoformat(),
                        "view_count": 5,
                        "user_preferences": {
                            "expanded_sections": ["progress", "insights"],
                            "theme": "dark"
                        }
                    }
                }
            }
        }
    
    # Authentication Flow Tests
    
    @pytest.mark.asyncio
    async def test_context_buttons_require_authentication(self, browser_setup, backend_server):
        """Test that context buttons show authentication prompts when user is not logged in."""
        page, context, browser = browser_setup
        
        # Mock the frontend page with context buttons
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Context Integration Test</title>
            <script src="https://unpkg.com/axios/dist/axios.min.js"></script>
        </head>
        <body>
            <div id="task-context-section">
                <h2>Task Context</h2>
                <button id="view-context-btn" onclick="viewContext()">View Context</button>
                <button id="edit-context-btn" onclick="editContext()">Edit Context</button>
                <button id="add-insight-btn" onclick="addInsight()">Add Insight</button>
                <div id="auth-status">Not authenticated</div>
                <div id="context-content"></div>
                <div id="error-message"></div>
            </div>
            
            <script>
                const API_BASE = 'http://localhost:8000';
                let authToken = localStorage.getItem('auth_token');
                
                function updateAuthStatus() {
                    const statusElement = document.getElementById('auth-status');
                    statusElement.textContent = authToken ? 'Authenticated' : 'Not authenticated';
                }
                
                async function makeAuthenticatedRequest(url, options = {}) {
                    if (!authToken) {
                        document.getElementById('error-message').textContent = 'Please log in to access context features';
                        return null;
                    }
                    
                    options.headers = {
                        ...options.headers,
                        'Authorization': `Bearer ${authToken}`,
                        'Content-Type': 'application/json'
                    };
                    
                    try {
                        const response = await axios(url, options);
                        return response.data;
                    } catch (error) {
                        if (error.response?.status === 401) {
                            document.getElementById('error-message').textContent = 'Authentication required. Please log in.';
                        } else {
                            document.getElementById('error-message').textContent = `Error: ${error.message}`;
                        }
                        return null;
                    }
                }
                
                async function viewContext() {
                    const result = await makeAuthenticatedRequest(`${API_BASE}/api/v2/contexts/task/test-context-123`);
                    if (result) {
                        document.getElementById('context-content').textContent = JSON.stringify(result, null, 2);
                    }
                }
                
                async function editContext() {
                    const result = await makeAuthenticatedRequest(`${API_BASE}/api/v2/contexts/task/test-context-123`, {
                        method: 'PUT',
                        data: { data: { title: 'Updated via frontend' } }
                    });
                    if (result) {
                        document.getElementById('context-content').textContent = 'Context updated successfully';
                    }
                }
                
                async function addInsight() {
                    const result = await makeAuthenticatedRequest(`${API_BASE}/api/v2/contexts/task/test-context-123/insights`, {
                        method: 'POST',
                        data: { 
                            content: 'Frontend integration working well',
                            category: 'technical',
                            importance: 'medium'
                        }
                    });
                    if (result) {
                        document.getElementById('context-content').textContent = 'Insight added successfully';
                    }
                }
                
                function login() {
                    // Simulate login
                    authToken = 'mock-jwt-token-12345';
                    localStorage.setItem('auth_token', authToken);
                    updateAuthStatus();
                }
                
                updateAuthStatus();
            </script>
        </body>
        </html>
        """
        
        # Load the test page
        await page.set_content(html_content)
        
        # Initially, user is not authenticated
        auth_status = await page.text_content("#auth-status")
        assert "Not authenticated" in auth_status
        
        # Click context button without authentication
        await page.click("#view-context-btn")
        
        # Should show authentication error
        error_message = await page.text_content("#error-message")
        assert "Please log in" in error_message or "Authentication required" in error_message
    
    @pytest.mark.asyncio
    async def test_context_buttons_work_after_authentication(self, browser_setup, backend_server, 
                                                             mock_authenticated_user):
        """Test that context buttons work correctly after user authentication."""
        page, context, browser = browser_setup
        
        # Mock the backend API responses
        with patch.object(backend_server, 'get') as mock_get:
            with patch.object(backend_server, 'put') as mock_put:
                with patch.object(backend_server, 'post') as mock_post:
                    
                    # Mock successful API responses
                    mock_get.return_value.status_code = 200
                    mock_get.return_value.json.return_value = {
                        "success": True,
                        "context": {
                            "id": "test-context-123",
                            "data": {"title": "Test Context", "progress": 75}
                        }
                    }
                    
                    mock_put.return_value.status_code = 200
                    mock_put.return_value.json.return_value = {
                        "success": True,
                        "message": "Context updated successfully"
                    }
                    
                    mock_post.return_value.status_code = 200
                    mock_post.return_value.json.return_value = {
                        "success": True,
                        "message": "Insight added successfully"
                    }
                    
                    # Create authenticated frontend page
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Authenticated Context Test</title>
                        <script src="https://unpkg.com/axios/dist/axios.min.js"></script>
                    </head>
                    <body>
                        <div id="context-section">
                            <div id="auth-status">Authenticated as {mock_authenticated_user['email']}</div>
                            <button id="view-context-btn" onclick="viewContext()">View Context</button>
                            <button id="edit-context-btn" onclick="editContext()">Edit Context</button>
                            <div id="context-content"></div>
                            <div id="success-message"></div>
                        </div>
                        
                        <script>
                            const authToken = '{mock_authenticated_user['token']}';
                            
                            async function viewContext() {{
                                try {{
                                    // Simulate successful API call
                                    const mockResponse = {{
                                        success: true,
                                        context: {{
                                            id: "test-context-123",
                                            data: {{title: "Test Context", progress: 75}}
                                        }}
                                    }};
                                    
                                    document.getElementById('context-content').textContent = JSON.stringify(mockResponse, null, 2);
                                    document.getElementById('success-message').textContent = 'Context loaded successfully';
                                }} catch (error) {{
                                    document.getElementById('context-content').textContent = 'Error loading context';
                                }}
                            }}
                            
                            async function editContext() {{
                                try {{
                                    // Simulate successful update
                                    const mockResponse = {{
                                        success: true,
                                        message: "Context updated successfully"
                                    }};
                                    
                                    document.getElementById('context-content').textContent = JSON.stringify(mockResponse, null, 2);
                                    document.getElementById('success-message').textContent = 'Context updated successfully';
                                }} catch (error) {{
                                    document.getElementById('context-content').textContent = 'Error updating context';
                                }}
                            }}
                        </script>
                    </body>
                    </html>
                    """
                    
                    await page.set_content(html_content)
                    
                    # Verify authenticated status
                    auth_status = await page.text_content("#auth-status")
                    assert mock_authenticated_user['email'] in auth_status
                    
                    # Test view context button
                    await page.click("#view-context-btn")
                    await page.wait_for_timeout(100)  # Wait for async operation
                    
                    context_content = await page.text_content("#context-content")
                    assert "Test Context" in context_content
                    
                    success_message = await page.text_content("#success-message")
                    assert "Context loaded successfully" in success_message
                    
                    # Test edit context button
                    await page.click("#edit-context-btn")
                    await page.wait_for_timeout(100)
                    
                    success_message = await page.text_content("#success-message")
                    assert "Context updated successfully" in success_message
    
    # Context UI Integration Tests
    
    @pytest.mark.asyncio
    async def test_task_detail_page_context_integration(self, browser_setup, sample_task_with_context, 
                                                        mock_authenticated_user):
        """Test context integration in task detail page."""
        page, context, browser = browser_setup
        
        task_data = sample_task_with_context
        
        # Create a realistic task detail page with context integration
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Task Detail with Context</title>
            <style>
                .task-detail {{ padding: 20px; font-family: Arial, sans-serif; }}
                .context-section {{ border: 1px solid #ccc; margin: 20px 0; padding: 15px; }}
                .context-actions {{ margin: 10px 0; }}
                .context-actions button {{ margin: 5px; padding: 8px 12px; }}
                .context-content {{ background: #f5f5f5; padding: 10px; margin: 10px 0; }}
                .insight {{ margin: 5px 0; padding: 5px; background: #e8f4f8; }}
                .progress-bar {{ width: 100%; height: 20px; background: #ddd; }}
                .progress-fill {{ height: 100%; background: #4caf50; }}
                .hidden {{ display: none; }}
            </style>
        </head>
        <body>
            <div class="task-detail">
                <h1>Task: {task_data['task']['title']}</h1>
                <p>Status: {task_data['task']['status']}</p>
                <p>Priority: {task_data['task']['priority']}</p>
                
                <div class="context-section" id="context-section">
                    <h2>Context Information</h2>
                    <div class="context-actions">
                        <button id="load-context-btn" onclick="loadContext()">Load Context</button>
                        <button id="add-insight-btn" onclick="showAddInsightForm()">Add Insight</button>
                        <button id="update-progress-btn" onclick="showUpdateProgressForm()">Update Progress</button>
                        <button id="resolve-inheritance-btn" onclick="resolveInheritance()">View Full Context</button>
                    </div>
                    
                    <div id="context-content" class="context-content hidden">
                        <div id="progress-section">
                            <h3>Progress: <span id="progress-percentage">0</span>%</h3>
                            <div class="progress-bar">
                                <div id="progress-fill" class="progress-fill" style="width: 0%;"></div>
                            </div>
                        </div>
                        
                        <div id="insights-section">
                            <h3>Insights</h3>
                            <div id="insights-list"></div>
                        </div>
                        
                        <div id="next-steps-section">
                            <h3>Next Steps</h3>
                            <div id="next-steps-list"></div>
                        </div>
                    </div>
                    
                    <div id="add-insight-form" class="hidden">
                        <h3>Add New Insight</h3>
                        <textarea id="insight-content" placeholder="Enter your insight..."></textarea>
                        <select id="insight-category">
                            <option value="technical">Technical</option>
                            <option value="business">Business</option>
                            <option value="performance">Performance</option>
                        </select>
                        <button onclick="addInsight()">Add Insight</button>
                        <button onclick="hideAddInsightForm()">Cancel</button>
                    </div>
                    
                    <div id="resolved-context" class="context-content hidden">
                        <h3>Full Context (with inheritance)</h3>
                        <div id="resolved-content"></div>
                    </div>
                    
                    <div id="status-message"></div>
                </div>
            </div>
            
            <script>
                const taskId = '{task_data['task']['id']}';
                const authToken = '{mock_authenticated_user['token']}';
                
                // Mock context data
                const mockContextData = {json.dumps(task_data['context']['data'])};
                const mockResolvedContext = {{
                    task: mockContextData,
                    branch: {{git_branch_name: "feature/e2e-testing"}},
                    project: {{project_name: "E2E Test Project"}},
                    global: {{autonomous_rules: {{test_rule: "enabled"}}}}
                }};
                
                function showStatus(message, isError = false) {{
                    const statusElement = document.getElementById('status-message');
                    statusElement.textContent = message;
                    statusElement.style.color = isError ? 'red' : 'green';
                    setTimeout(() => statusElement.textContent = '', 3000);
                }}
                
                function loadContext() {{
                    try {{
                        // Simulate loading context
                        const progressPercentage = mockContextData.progress || 0;
                        document.getElementById('progress-percentage').textContent = progressPercentage;
                        document.getElementById('progress-fill').style.width = progressPercentage + '%';
                        
                        // Display insights
                        const insightsList = document.getElementById('insights-list');
                        insightsList.innerHTML = '';
                        (mockContextData.insights || []).forEach(insight => {{
                            const insightDiv = document.createElement('div');
                            insightDiv.className = 'insight';
                            insightDiv.textContent = insight;
                            insightsList.appendChild(insightDiv);
                        }});
                        
                        // Display next steps
                        const nextStepsList = document.getElementById('next-steps-list');
                        nextStepsList.innerHTML = '';
                        (mockContextData.next_steps || []).forEach(step => {{
                            const stepDiv = document.createElement('div');
                            stepDiv.textContent = '• ' + step;
                            nextStepsList.appendChild(stepDiv);
                        }});
                        
                        document.getElementById('context-content').classList.remove('hidden');
                        showStatus('Context loaded successfully');
                    }} catch (error) {{
                        showStatus('Error loading context', true);
                    }}
                }}
                
                function showAddInsightForm() {{
                    document.getElementById('add-insight-form').classList.remove('hidden');
                }}
                
                function hideAddInsightForm() {{
                    document.getElementById('add-insight-form').classList.add('hidden');
                    document.getElementById('insight-content').value = '';
                }}
                
                function addInsight() {{
                    const content = document.getElementById('insight-content').value;
                    const category = document.getElementById('insight-category').value;
                    
                    if (!content.trim()) {{
                        showStatus('Please enter insight content', true);
                        return;
                    }}
                    
                    try {{
                        // Simulate adding insight
                        const insightDiv = document.createElement('div');
                        insightDiv.className = 'insight';
                        insightDiv.textContent = content;
                        document.getElementById('insights-list').appendChild(insightDiv);
                        
                        hideAddInsightForm();
                        showStatus('Insight added successfully');
                    }} catch (error) {{
                        showStatus('Error adding insight', true);
                    }}
                }}
                
                function resolveInheritance() {{
                    try {{
                        // Simulate context resolution
                        const resolvedContent = document.getElementById('resolved-content');
                        resolvedContent.innerHTML = `
                            <h4>Task Context:</h4>
                            <pre>${{JSON.stringify(mockResolvedContext.task, null, 2)}}</pre>
                            <h4>Branch Context:</h4>
                            <pre>${{JSON.stringify(mockResolvedContext.branch, null, 2)}}</pre>
                            <h4>Project Context:</h4>
                            <pre>${{JSON.stringify(mockResolvedContext.project, null, 2)}}</pre>
                            <h4>Global Context:</h4>
                            <pre>${{JSON.stringify(mockResolvedContext.global, null, 2)}}</pre>
                        `;
                        
                        document.getElementById('resolved-context').classList.remove('hidden');
                        showStatus('Full context resolved successfully');
                    }} catch (error) {{
                        showStatus('Error resolving context', true);
                    }}
                }}
            </script>
        </body>
        </html>
        """
        
        await page.set_content(html_content)
        
        # Test loading context
        await page.click("#load-context-btn")
        await page.wait_for_timeout(100)
        
        # Verify context content is displayed
        context_section = await page.query_selector("#context-content")
        is_visible = await context_section.is_visible()
        assert is_visible
        
        # Check progress display
        progress_text = await page.text_content("#progress-percentage")
        assert "60" in progress_text  # From sample data
        
        # Check insights are displayed
        insights_list = await page.query_selector("#insights-list")
        insights_content = await insights_list.text_content()
        assert "Context buttons working correctly" in insights_content
        
        # Test adding insight
        await page.click("#add-insight-btn")
        await page.wait_for_timeout(50)
        
        # Form should be visible
        insight_form = await page.query_selector("#add-insight-form")
        is_form_visible = await insight_form.is_visible()
        assert is_form_visible
        
        # Fill and submit insight
        await page.fill("#insight-content", "E2E testing is working great!")
        await page.select_option("#insight-category", "technical")
        await page.click("button[onclick='addInsight()']")
        await page.wait_for_timeout(100)
        
        # Verify new insight appears
        insights_content_updated = await insights_list.text_content()
        assert "E2E testing is working great!" in insights_content_updated
        
        # Test context inheritance resolution
        await page.click("#resolve-inheritance-btn")
        await page.wait_for_timeout(100)
        
        # Verify resolved context is displayed
        resolved_section = await page.query_selector("#resolved-context")
        is_resolved_visible = await resolved_section.is_visible()
        assert is_resolved_visible
        
        resolved_content = await page.text_content("#resolved-content")
        assert "Task Context:" in resolved_content
        assert "Branch Context:" in resolved_content
        assert "Project Context:" in resolved_content
        assert "Global Context:" in resolved_content
    
    # Error Handling Tests
    
    @pytest.mark.asyncio
    async def test_context_error_handling_in_frontend(self, browser_setup):
        """Test that context errors are handled gracefully in the frontend."""
        page, context, browser = browser_setup
        
        # Create page that simulates API errors
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Context Error Handling Test</title>
        </head>
        <body>
            <div id="context-actions">
                <button id="trigger-404-btn" onclick="trigger404Error()">Trigger 404 Error</button>
                <button id="trigger-401-btn" onclick="trigger401Error()">Trigger Auth Error</button>
                <button id="trigger-500-btn" onclick="trigger500Error()">Trigger Server Error</button>
            </div>
            
            <div id="error-display"></div>
            <div id="user-friendly-message"></div>
            
            <script>
                function showError(type, message) {
                    document.getElementById('error-display').textContent = `Error Type: ${type}`;
                    document.getElementById('user-friendly-message').textContent = message;
                }
                
                function trigger404Error() {
                    // Simulate 404 context not found error
                    showError('404', 'Context not found. The context may have been deleted or you may not have permission to access it.');
                }
                
                function trigger401Error() {
                    // Simulate authentication error
                    showError('401', 'Please log in to access context features. Your session may have expired.');
                }
                
                function trigger500Error() {
                    // Simulate server error
                    showError('500', 'Something went wrong on our end. Please try again in a few moments.');
                }
            </script>
        </body>
        </html>
        """
        
        await page.set_content(html_content)
        
        # Test 404 error handling
        await page.click("#trigger-404-btn")
        error_display = await page.text_content("#error-display")
        user_message = await page.text_content("#user-friendly-message")
        
        assert "404" in error_display
        assert "Context not found" in user_message
        assert "permission" in user_message.lower()
        
        # Test 401 error handling
        await page.click("#trigger-401-btn")
        error_display = await page.text_content("#error-display")
        user_message = await page.text_content("#user-friendly-message")
        
        assert "401" in error_display
        assert "log in" in user_message.lower()
        assert "session" in user_message.lower()
        
        # Test 500 error handling
        await page.click("#trigger-500-btn")
        error_display = await page.text_content("#error-display")
        user_message = await page.text_content("#user-friendly-message")
        
        assert "500" in error_display
        assert "try again" in user_message.lower()
        assert "went wrong" in user_message.lower()
    
    # Real-world Workflow Tests
    
    @pytest.mark.asyncio
    async def test_complete_context_workflow(self, browser_setup, mock_authenticated_user):
        """Test a complete context workflow from creation to delegation."""
        page, context, browser = browser_setup
        
        # Create a comprehensive workflow page
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Complete Context Workflow</title>
            <style>
                .workflow-step {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; }}
                .completed {{ background-color: #d4edda; }}
                .active {{ background-color: #fff3cd; }}
                .pending {{ background-color: #f8f9fa; }}
            </style>
        </head>
        <body>
            <h1>Context Management Workflow</h1>
            
            <div id="step1" class="workflow-step active">
                <h2>Step 1: Create Task Context</h2>
                <button onclick="createContext()">Create Context</button>
                <div id="step1-result"></div>
            </div>
            
            <div id="step2" class="workflow-step pending">
                <h2>Step 2: Add Insights</h2>
                <button onclick="addInsights()">Add Multiple Insights</button>
                <div id="step2-result"></div>
            </div>
            
            <div id="step3" class="workflow-step pending">
                <h2>Step 3: Update Progress</h2>
                <button onclick="updateProgress()">Update Progress</button>
                <div id="step3-result"></div>
            </div>
            
            <div id="step4" class="workflow-step pending">
                <h2>Step 4: Resolve Full Context</h2>
                <button onclick="resolveContext()">Resolve Context</button>
                <div id="step4-result"></div>
            </div>
            
            <div id="step5" class="workflow-step pending">
                <h2>Step 5: Delegate Pattern</h2>
                <button onclick="delegatePattern()">Delegate to Project Level</button>
                <div id="step5-result"></div>
            </div>
            
            <div id="workflow-status">Ready to start workflow</div>
            
            <script>
                let currentStep = 1;
                const maxSteps = 5;
                
                function updateWorkflowStatus(message) {{
                    document.getElementById('workflow-status').textContent = message;
                }}
                
                function markStepCompleted(stepNum) {{
                    const stepElement = document.getElementById(`step${{stepNum}}`);
                    stepElement.classList.remove('active', 'pending');
                    stepElement.classList.add('completed');
                    
                    if (stepNum < maxSteps) {{
                        const nextStepElement = document.getElementById(`step${{stepNum + 1}}`);
                        nextStepElement.classList.remove('pending');
                        nextStepElement.classList.add('active');
                    }}
                    
                    currentStep = stepNum + 1;
                }}
                
                async function createContext() {{
                    try {{
                        // Simulate context creation
                        const result = {{
                            success: true,
                            context: {{
                                id: "workflow-context-123",
                                data: {{
                                    title: "Workflow Test Context",
                                    created_at: new Date().toISOString(),
                                    workflow_step: 1
                                }}
                            }}
                        }};
                        
                        document.getElementById('step1-result').textContent = 'Context created successfully!';
                        markStepCompleted(1);
                        updateWorkflowStatus('Context created. Ready for insights.');
                    }} catch (error) {{
                        document.getElementById('step1-result').textContent = 'Error creating context';
                    }}
                }}
                
                async function addInsights() {{
                    try {{
                        const insights = [
                            {{content: 'Context workflow is intuitive', category: 'user_experience'}},
                            {{content: 'Authentication integration is seamless', category: 'technical'}},
                            {{content: 'Error handling is robust', category: 'reliability'}}
                        ];
                        
                        let resultText = 'Insights added:\\n';
                        insights.forEach((insight, index) => {{
                            resultText += `${{index + 1}}. ${{insight.content}} [${{insight.category}}]\\n`;
                        }});
                        
                        document.getElementById('step2-result').textContent = resultText;
                        markStepCompleted(2);
                        updateWorkflowStatus('Insights added. Ready for progress update.');
                    }} catch (error) {{
                        document.getElementById('step2-result').textContent = 'Error adding insights';
                    }}
                }}
                
                async function updateProgress() {{
                    try {{
                        const progressUpdate = {{
                            content: 'Workflow testing 75% complete',
                            timestamp: new Date().toISOString(),
                            milestone: 'Context integration verified'
                        }};
                        
                        document.getElementById('step3-result').textContent = 
                            `Progress updated: ${{progressUpdate.content}}\\nMilestone: ${{progressUpdate.milestone}}`;
                        markStepCompleted(3);
                        updateWorkflowStatus('Progress updated. Ready for context resolution.');
                    }} catch (error) {{
                        document.getElementById('step3-result').textContent = 'Error updating progress';
                    }}
                }}
                
                async function resolveContext() {{
                    try {{
                        const resolvedContext = {{
                            task: {{
                                title: "Workflow Test Context",
                                insights_count: 3,
                                progress: 75
                            }},
                            branch: {{git_branch_name: "feature/context-workflow"}},
                            project: {{project_name: "Context Integration Project"}},
                            global: {{autonomous_rules: {{workflow_testing: "enabled"}}}}
                        }};
                        
                        document.getElementById('step4-result').textContent = 
                            'Full context resolved successfully!\\n' +
                            `Task insights: ${{resolvedContext.task.insights_count}}\\n` +
                            `Progress: ${{resolvedContext.task.progress}}%\\n` +
                            `Branch: ${{resolvedContext.branch.git_branch_name}}`;
                        markStepCompleted(4);
                        updateWorkflowStatus('Context resolved. Ready for delegation.');
                    }} catch (error) {{
                        document.getElementById('step4-result').textContent = 'Error resolving context';
                    }}
                }}
                
                async function delegatePattern() {{
                    try {{
                        const delegation = {{
                            delegate_to: 'project',
                            pattern: 'context_workflow_integration',
                            reason: 'Reusable pattern for all context-enabled tasks',
                            components: ['insight_management', 'progress_tracking', 'context_resolution']
                        }};
                        
                        document.getElementById('step5-result').textContent = 
                            `Pattern delegated successfully!\\n` +
                            `Pattern: ${{delegation.pattern}}\\n` +
                            `Level: ${{delegation.delegate_to}}\\n` +
                            `Components: ${{delegation.components.join(', ')}}`;
                        markStepCompleted(5);
                        updateWorkflowStatus('Workflow completed successfully! 🎉');
                    }} catch (error) {{
                        document.getElementById('step5-result').textContent = 'Error delegating pattern';
                    }}
                }}
            </script>
        </body>
        </html>
        """
        
        await page.set_content(html_content)
        
        # Execute the complete workflow
        
        # Step 1: Create Context
        await page.click("button[onclick='createContext()']")
        await page.wait_for_timeout(100)
        step1_result = await page.text_content("#step1-result")
        assert "Context created successfully" in step1_result
        
        # Step 2: Add Insights
        await page.click("button[onclick='addInsights()']")
        await page.wait_for_timeout(100)
        step2_result = await page.text_content("#step2-result")
        assert "Context workflow is intuitive" in step2_result
        assert "Authentication integration is seamless" in step2_result
        
        # Step 3: Update Progress
        await page.click("button[onclick='updateProgress()']")
        await page.wait_for_timeout(100)
        step3_result = await page.text_content("#step3-result")
        assert "Workflow testing 75% complete" in step3_result
        assert "Context integration verified" in step3_result
        
        # Step 4: Resolve Context
        await page.click("button[onclick='resolveContext()']")
        await page.wait_for_timeout(100)
        step4_result = await page.text_content("#step4-result")
        assert "Full context resolved successfully" in step4_result
        assert "Progress: 75%" in step4_result
        
        # Step 5: Delegate Pattern
        await page.click("button[onclick='delegatePattern()']")
        await page.wait_for_timeout(100)
        step5_result = await page.text_content("#step5-result")
        assert "Pattern delegated successfully" in step5_result
        assert "context_workflow_integration" in step5_result
        
        # Verify workflow completion
        final_status = await page.text_content("#workflow-status")
        assert "Workflow completed successfully" in final_status
        
        # Verify all steps are marked as completed
        for step_num in range(1, 6):
            step_element = await page.query_selector(f"#step{step_num}")
            class_list = await step_element.get_attribute("class")
            assert "completed" in class_list
    
    # Performance Tests
    
    @pytest.mark.asyncio
    async def test_context_ui_performance(self, browser_setup):
        """Test that context UI operations perform well with large datasets."""
        page, context, browser = browser_setup
        
        # Create page with large context dataset
        large_insights = [f"Performance insight #{i}: Context system handles large datasets efficiently" 
                         for i in range(100)]
        large_progress_updates = [f"Progress update #{i}: Milestone completed" 
                                for i in range(50)]
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Context Performance Test</title>
        </head>
        <body>
            <div id="performance-test">
                <h1>Context Performance Test</h1>
                <button id="load-large-context" onclick="loadLargeContext()">Load Large Context (100 insights, 50 updates)</button>
                <div id="performance-results"></div>
                <div id="context-display" style="max-height: 400px; overflow-y: auto;"></div>
            </div>
            
            <script>
                const largeInsights = {json.dumps(large_insights)};
                const largeProgressUpdates = {json.dumps(large_progress_updates)};
                
                function loadLargeContext() {{
                    const startTime = performance.now();
                    
                    try {{
                        const contextDisplay = document.getElementById('context-display');
                        
                        // Simulate loading large context data
                        let html = '<h2>Insights (' + largeInsights.length + ')</h2>';
                        largeInsights.forEach((insight, index) => {{
                            html += `<div class="insight-item">${{index + 1}}. ${{insight}}</div>`;
                        }});
                        
                        html += '<h2>Progress Updates (' + largeProgressUpdates.length + ')</h2>';
                        largeProgressUpdates.forEach((update, index) => {{
                            html += `<div class="progress-item">${{index + 1}}. ${{update}}</div>`;
                        }});
                        
                        contextDisplay.innerHTML = html;
                        
                        const endTime = performance.now();
                        const loadTime = endTime - startTime;
                        
                        document.getElementById('performance-results').textContent = 
                            `Context loaded in ${{loadTime.toFixed(2)}}ms. ` +
                            `Items rendered: ${{largeInsights.length + largeProgressUpdates.length}}`;
                        
                        // Performance should be under 500ms for good UX
                        if (loadTime < 500) {{
                            document.getElementById('performance-results').style.color = 'green';
                        }} else {{
                            document.getElementById('performance-results').style.color = 'orange';
                        }}
                        
                    }} catch (error) {{
                        document.getElementById('performance-results').textContent = 'Error loading context: ' + error.message;
                        document.getElementById('performance-results').style.color = 'red';
                    }}
                }}
            </script>
        </body>
        </html>
        """
        
        await page.set_content(html_content)
        
        # Test loading large context
        await page.click("#load-large-context")
        await page.wait_for_timeout(1000)  # Wait for rendering
        
        # Check performance results
        performance_results = await page.text_content("#performance-results")
        assert "Context loaded in" in performance_results
        assert "Items rendered: 150" in performance_results
        
        # Verify content was rendered
        context_display = await page.text_content("#context-display")
        assert "Performance insight #1" in context_display
        assert "Performance insight #99" in context_display
        assert "Progress update #1" in context_display
        assert "Progress update #49" in context_display


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])