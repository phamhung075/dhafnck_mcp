// API service for MCP Task Management
// Handles CRUD for tasks, subtasks, and dependencies

const API_BASE = "http://localhost:8000/mcp";

// --- Interfaces for Type Safety ---
export interface Task {
    id: string;
    title: string;
    description: string;
    status: string;
    priority: string;
    subtasks: Subtask[];
    [key: string]: any;
}

export interface Subtask {
    id: string;
    title: string;
    description: string;
    status: string;
    priority: string;
    [key: string]: any;
}

export interface Project {
    id: string;
    name: string;
    description: string;
    task_trees: Record<string, Branch>;
}

export interface Branch {
    id: string;
    name: string;
    description: string;
}

// --- API Fetch Functions ---

// Function to fetch all projects
export async function fetchProjects(): Promise<Project[]> {
    return listProjects();
}

// Function to fetch details for a single project, including branches (task trees)
export async function fetchProjectDetails(projectId: string): Promise<Project | null> {
    return getProject(projectId);
}


// Function to fetch tasks for a specific project and branch
export async function fetchTasks(projectId: string, branchName: string): Promise<Task[]> {
    return listTasks({ project_id: projectId, git_branch_name: branchName });
}

// Function to fetch subtasks for a specific task
export async function fetchSubtasks(_projectId: string, _branchName: string, taskId: string): Promise<Subtask[]> {
    return listSubtasks(taskId);
}

export type Rule = {
  id: string;
  name: string;
  description?: string;
  type?: string;
  content?: string;
  [key: string]: any;
};

let rpcId = 1;

function getRpcId() {
  return rpcId++;
}

const DEFAULTS = {
  project_id: "default_project",
  git_branch_name: "main",
  user_id: "default_id",
};

// --- MCP Protocol Headers Helper ---
const MCP_HEADERS = {
  "Content-Type": "application/json",
  "Accept": "application/json, text/event-stream",
  "MCP-Protocol-Version": "2025-06-18",
};

function withMcpHeaders(extra: Record<string, string> = {}) {
  return { ...MCP_HEADERS, ...extra };
}

// --- Task Management ---
export async function listTasks(params: any = {}): Promise<Task[]> {
  const { git_branch_id, project_id = "default_project", git_branch_name = "main", user_id = "default_id", ...rest } = params;
  const filteredParams = {
    action: "list",
    git_branch_id: git_branch_id || git_branch_name,
    ...rest
  };
  const body = {
    jsonrpc: "2.0",
    method: "tools/call",
    params: {
      name: "manage_task",
      arguments: filteredParams
    },
    id: getRpcId(),
  };
  const res = await fetch(`${API_BASE}`, {
    method: "POST",
    headers: withMcpHeaders(),
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (data.result && data.result.content && Array.isArray(data.result.content) && data.result.content.length > 0) {
    try {
      const toolResult = JSON.parse(data.result.content[0].text);
      if (toolResult.success && Array.isArray(toolResult.tasks)) {
        return toolResult.tasks;
      }
    } catch {}
  }
  return [];
}

export async function getTask(task_id: string): Promise<Task | null> {
  const body = {
    jsonrpc: "2.0",
    method: "tools/call",
    params: {
      name: "manage_task",
      arguments: { action: "get", task_id }
    },
    id: getRpcId(),
  };
  const res = await fetch(`${API_BASE}`, {
    method: "POST",
    headers: withMcpHeaders(),
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (data.result && data.result.content && Array.isArray(data.result.content) && data.result.content.length > 0) {
    try {
      const toolResult = JSON.parse(data.result.content[0].text);
      if (toolResult.success && toolResult.task) {
        return toolResult.task;
      }
    } catch {}
  }
  return null;
}

export async function createTask(task: Partial<Task>): Promise<Task | null> {
  const body = {
    jsonrpc: "2.0",
    method: "tools/call",
    params: {
      name: "manage_task",
      arguments: { action: "create", ...task }
    },
    id: getRpcId(),
  };
  const res = await fetch(`${API_BASE}`, {
    method: "POST",
    headers: withMcpHeaders(),
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (data.result && data.result.content && Array.isArray(data.result.content) && data.result.content.length > 0) {
    try {
      const toolResult = JSON.parse(data.result.content[0].text);
      if (toolResult.success && toolResult.task) {
        return toolResult.task;
      }
    } catch {}
  }
  return null;
}

export async function updateTask(task_id: string, updates: Partial<Task>): Promise<Task | null> {
  const body = {
    jsonrpc: "2.0",
    method: "tools/call",
    params: {
      name: "manage_task",
      arguments: { action: "update", task_id, ...updates }
    },
    id: getRpcId(),
  };
  const res = await fetch(`${API_BASE}`, {
    method: "POST",
    headers: withMcpHeaders(),
    body: JSON.stringify(body),
  });
  const data = await res.json();
  
  
  if (data.result && data.result.content && Array.isArray(data.result.content) && data.result.content.length > 0) {
    try {
      const toolResult = JSON.parse(data.result.content[0].text);
      
      // Check if success is true, even if task is not returned
      if (toolResult.success) {
        // Return a dummy task object if task is not in response
        return toolResult.task || { id: task_id, ...updates } as Task;
      }
      
      // If not successful, check for error message
      if (toolResult.error) {
        const errorMessage = typeof toolResult.error === 'string' 
          ? toolResult.error 
          : toolResult.error.message || JSON.stringify(toolResult.error);
        throw new Error(errorMessage);
      }
      
      // If no success and no error
      throw new Error('Unexpected response from server');
    } catch (e) {
      // If it's already an Error, throw it, otherwise create a new Error
      if (e instanceof Error) {
        throw e;
      } else {
        throw new Error(String(e));
      }
    }
  }
  
  // Check for error in response
  if (data.error) {
    throw new Error(data.error.message || 'Unknown error');
  }
  
  return null;
}

export async function deleteTask(task_id: string): Promise<boolean> {
  const body = {
    jsonrpc: "2.0",
    method: "tools/call",
    params: {
      name: "manage_task",
      arguments: { action: "delete", task_id }
    },
    id: getRpcId(),
  };
  const res = await fetch(`${API_BASE}`, {
    method: "POST",
    headers: withMcpHeaders(),
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (data.result && data.result.content && Array.isArray(data.result.content) && data.result.content.length > 0) {
    try {
      const toolResult = JSON.parse(data.result.content[0].text);
      if (toolResult.success) {
        return true;
      }
    } catch {}
  }
  return false;
}

// --- Subtask Management ---
export async function listSubtasks(task_id: string): Promise<any[]> {
  const body = {
    jsonrpc: "2.0",
    method: "tools/call",
    params: {
      name: "manage_subtask",
      arguments: { action: "list", task_id }
    },
    id: getRpcId(),
  };
  const res = await fetch(`${API_BASE}`, {
    method: "POST",
    headers: withMcpHeaders(),
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (data.result && data.result.content && Array.isArray(data.result.content) && data.result.content.length > 0) {
    try {
      const toolResult = JSON.parse(data.result.content[0].text);
      if (toolResult.success && Array.isArray(toolResult.subtasks)) {
        return toolResult.subtasks;
      }
    } catch {}
  }
  return [];
}

export async function createSubtask(task_id: string, subtask: any): Promise<any> {
  const body = {
    jsonrpc: "2.0",
    method: "tools/call",
    params: {
      name: "manage_subtask",
      arguments: { action: "create", task_id, ...subtask }
    },
    id: getRpcId(),
  };
  const res = await fetch(`${API_BASE}`, {
    method: "POST",
    headers: withMcpHeaders(),
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (data.result && data.result.content && Array.isArray(data.result.content) && data.result.content.length > 0) {
    try {
      const toolResult = JSON.parse(data.result.content[0].text);
      if (toolResult.success && toolResult.subtask) {
        return toolResult.subtask;
      }
    } catch {}
  }
  return null;
}

export async function updateSubtask(task_id: string, id: string, updates: any): Promise<any> {
  const body = {
    jsonrpc: "2.0",
    method: "tools/call",
    params: {
      name: "manage_subtask",
      arguments: { action: "update", task_id, subtask_id: id, ...updates }
    },
    id: getRpcId(),
  };
  const res = await fetch(`${API_BASE}`, {
    method: "POST",
    headers: withMcpHeaders(),
    body: JSON.stringify(body),
  });
  const data = await res.json();
  
  
  if (data.result && data.result.content && Array.isArray(data.result.content) && data.result.content.length > 0) {
    try {
      const toolResult = JSON.parse(data.result.content[0].text);
      
      if (toolResult.success) {
        return toolResult.subtask || { id, ...updates };
      }
      
      if (toolResult.error) {
        const errorMessage = typeof toolResult.error === 'string' 
          ? toolResult.error 
          : toolResult.error.message || JSON.stringify(toolResult.error);
        throw new Error(errorMessage);
      }
      
      throw new Error('Unexpected response from server');
    } catch (e) {
      if (e instanceof Error) {
        throw e;
      } else {
        throw new Error(String(e));
      }
    }
  }
  
  if (data.error) {
    throw new Error(data.error.message || 'Unknown error');
  }
  
  return null;
}

export async function deleteSubtask(task_id: string, id: string): Promise<boolean> {
  const body = {
    jsonrpc: "2.0",
    method: "tools/call",
    params: {
      name: "manage_subtask",
      arguments: { action: "delete", task_id, subtask_id: id }
    },
    id: getRpcId(),
  };
  const res = await fetch(`${API_BASE}`, {
    method: "POST",
    headers: withMcpHeaders(),
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (data.result && data.result.content && Array.isArray(data.result.content) && data.result.content.length > 0) {
    try {
      const toolResult = JSON.parse(data.result.content[0].text);
      if (toolResult.success) {
        return true;
      }
    } catch {}
  }
  return false;
}

// --- Dependency Management ---
export async function addDependency(task_id: string, dependency_id: string): Promise<boolean> {
  const body = {
    jsonrpc: "2.0",
    method: "tools/call",
    params: {
      name: "manage_task",
      arguments: { action: "add_dependency", task_id, dependency_id }
    },
    id: getRpcId(),
  };
  const res = await fetch(`${API_BASE}`, {
    method: "POST",
    headers: withMcpHeaders(),
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (data.result && data.result.content && Array.isArray(data.result.content) && data.result.content.length > 0) {
    try {
      const toolResult = JSON.parse(data.result.content[0].text);
      if (toolResult.success) {
        return true;
      }
    } catch {}
  }
  return false;
}

export async function removeDependency(task_id: string, dependency_id: string): Promise<boolean> {
  const body = {
    jsonrpc: "2.0",
    method: "tools/call",
    params: {
      name: "manage_task",
      arguments: { action: "remove_dependency", task_id, dependency_id }
    },
    id: getRpcId(),
  };
  const res = await fetch(`${API_BASE}`, {
    method: "POST",
    headers: withMcpHeaders(),
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (data.result && data.result.content && Array.isArray(data.result.content) && data.result.content.length > 0) {
    try {
      const toolResult = JSON.parse(data.result.content[0].text);
      if (toolResult.success) {
        return true;
      }
    } catch {}
  }
  return false;
}

// --- Context Management ---
export async function getTaskContext(task_id: string): Promise<any> {
  const body = {
    jsonrpc: "2.0",
    method: "tools/call",
    params: {
      name: "manage_hierarchical_context",
      arguments: { 
        action: "resolve",
        level: "task",
        context_id: task_id,
        force_refresh: false
      }
    },
    id: getRpcId(),
  };
  const res = await fetch(`${API_BASE}`, {
    method: "POST",
    headers: withMcpHeaders(),
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (data.result && data.result.content && Array.isArray(data.result.content) && data.result.content.length > 0) {
    try {
      const toolResult = JSON.parse(data.result.content[0].text);
      return toolResult;
    } catch (e) {
      console.error('Error parsing task context:', e);
    }
  }
  return null;
}

export async function getProjectContext(project_id: string): Promise<any> {
  const body = {
    jsonrpc: "2.0",
    method: "tools/call",
    params: {
      name: "manage_hierarchical_context",
      arguments: { 
        action: "resolve",
        level: "project",
        context_id: project_id,
        force_refresh: false
      }
    },
    id: getRpcId(),
  };
  const res = await fetch(`${API_BASE}`, {
    method: "POST",
    headers: withMcpHeaders(),
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (data.result && data.result.content && Array.isArray(data.result.content) && data.result.content.length > 0) {
    try {
      const toolResult = JSON.parse(data.result.content[0].text);
      return toolResult;
    } catch (e) {
      console.error('Error parsing project context:', e);
    }
  }
  return null;
}

// --- Project Management ---
export async function listProjects(): Promise<Project[]> {
  const body = {
    jsonrpc: "2.0",
    method: "tools/call",
    params: {
      name: "manage_project",
      arguments: { action: "list" }
    },
    id: getRpcId(),
  };
  const res = await fetch(`${API_BASE}`, {
    method: "POST",
    headers: withMcpHeaders(),
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (data.result && data.result.content && Array.isArray(data.result.content) && data.result.content.length > 0) {
    try {
      const toolResult = JSON.parse(data.result.content[0].text);
      if (toolResult.success && Array.isArray(toolResult.projects)) {
        // Get detailed project information including task_trees
        const projectsWithDetails = await Promise.all(
          toolResult.projects.map(async (project: any) => {
            const detailedProject = await getProject(project.id);
            return detailedProject || project;
          })
        );
        return projectsWithDetails;
      }
    } catch {}
  }
  return [];
}

export async function getProject(project_id: string): Promise<Project | null> {
  const body = {
    jsonrpc: "2.0",
    method: "tools/call",
    params: {
      name: "manage_project",
      arguments: { action: "get", project_id }
    },
    id: getRpcId(),
  };
  const res = await fetch(`${API_BASE}`, {
    method: "POST",
    headers: withMcpHeaders(),
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (data.result && data.result.content && Array.isArray(data.result.content) && data.result.content.length > 0) {
    try {
      const toolResult = JSON.parse(data.result.content[0].text);
      if (toolResult.success && toolResult.project) {
        return toolResult.project;
      }
    } catch {}
  }
  return null;
}

export async function createProject(project: Partial<Project>): Promise<Project | null> {
  const body = {
    jsonrpc: "2.0",
    method: "tools/call",
    params: {
      name: "manage_project",
      arguments: { action: "create", ...project }
    },
    id: getRpcId(),
  };
  const res = await fetch(`${API_BASE}`, {
    method: "POST",
    headers: withMcpHeaders(),
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (data.result && data.result.content && Array.isArray(data.result.content) && data.result.content.length > 0) {
    try {
      const toolResult = JSON.parse(data.result.content[0].text);
      if (toolResult.success && toolResult.project) {
        return toolResult.project;
      }
    } catch {}
  }
  return null;
}

export async function updateProject(project_id: string, updates: Partial<Project>): Promise<Project | null> {
  const body = {
    jsonrpc: "2.0",
    method: "tools/call",
    params: {
      name: "manage_project",
      arguments: { action: "update", project_id, ...updates }
    },
    id: getRpcId(),
  };
  const res = await fetch(`${API_BASE}`, {
    method: "POST",
    headers: withMcpHeaders(),
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (data.result && data.result.content && Array.isArray(data.result.content) && data.result.content.length > 0) {
    try {
      const toolResult = JSON.parse(data.result.content[0].text);
      if (toolResult.success && toolResult.project) {
        return toolResult.project;
      }
    } catch {}
  }
  return null;
}

export async function deleteProject(project_id: string): Promise<boolean> {
  const body = {
    jsonrpc: "2.0",
    method: "tools/call",
    params: {
      name: "manage_project",
      arguments: { action: "delete", project_id }
    },
    id: getRpcId(),
  };
  const res = await fetch(`${API_BASE}`, {
    method: "POST",
    headers: withMcpHeaders(),
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (data.result && data.result.content && Array.isArray(data.result.content) && data.result.content.length > 0) {
    try {
      const toolResult = JSON.parse(data.result.content[0].text);
      if (toolResult.success) {
        return true;
      }
    } catch {}
  }
  return false;
}

// --- Branch (Task Tree) Management ---
export async function listBranches(project_id: string): Promise<Branch[]> {
  const body = {
    jsonrpc: "2.0",
    method: "tools/call",
    params: {
      name: "manage_project",
      arguments: { action: "list" }
    },
    id: getRpcId(),
  };
  const res = await fetch(`${API_BASE}`, {
    method: "POST",
    headers: withMcpHeaders(),
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (data.result && data.result.content && Array.isArray(data.result.content) && data.result.content.length > 0) {
    try {
      const toolResult = JSON.parse(data.result.content[0].text);
      if (toolResult.success && Array.isArray(toolResult.projects)) {
        const project = toolResult.projects.find((p: any) => p.id === project_id);
        if (project && project.task_trees) {
          return Object.values(project.task_trees);
        }
      }
    } catch {}
  }
  return [];
}

// Function to create a new branch (task tree) for a project
export async function createBranch(projectId: string, branchName: string, description?: string): Promise<any> {
    const body = {
        jsonrpc: "2.0",
        method: "tools/call",
        params: {
            name: "manage_git_branch",
            arguments: { 
                action: "create",
                project_id: projectId,
                git_branch_name: branchName.toLowerCase().replace(/\s+/g, '-'), // Create a git-friendly name
                git_branch_description: description
            }
        },
        id: getRpcId(),
    };
    const res = await fetch(`${API_BASE}`, {
        method: "POST",
        headers: withMcpHeaders(),
        body: JSON.stringify(body),
    });
    const data = await res.json();
    if (data.result && data.result.content && Array.isArray(data.result.content) && data.result.content.length > 0) {
        try {
            const toolResult = JSON.parse(data.result.content[0].text);
            if (toolResult.success && toolResult.git_branch) {
                return toolResult.git_branch;
            }
        } catch {}
    }
    return null;
}

// NOTE: No update/delete branch API is documented. If MCP adds support, implement here.
export async function updateBranch(/* project_id: string, branch_id: string, updates: Partial<Branch> */): Promise<null> {
  // Not supported by MCP as of now
  return null;
}

export async function deleteBranch(/* project_id: string, branch_id: string */): Promise<boolean> {
  // Not supported by MCP as of now
  return false;
}

// --- Rule Management ---
export async function listRules(): Promise<Rule[]> {
  const body = {
    jsonrpc: "2.0",
    method: "tools/call",
    params: {
      name: "manage_rule",
      arguments: { action: "list" }
    },
    id: getRpcId(),
  };
  const res = await fetch(`${API_BASE}`, {
    method: "POST",
    headers: withMcpHeaders(),
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (data.result && data.result.content && Array.isArray(data.result.content) && data.result.content.length > 0) {
    try {
      const toolResult = JSON.parse(data.result.content[0].text);
      if (toolResult.success && Array.isArray(toolResult.rules)) {
        return toolResult.rules;
      }
    } catch {}
  }
  return [];
}

export async function getRule(rule_id: string): Promise<Rule | null> {
  const body = {
    jsonrpc: "2.0",
    method: "tools/call",
    params: {
      name: "manage_rule",
      arguments: { action: "info", target: rule_id }
    },
    id: getRpcId(),
  };
  const res = await fetch(`${API_BASE}`, {
    method: "POST",
    headers: withMcpHeaders(),
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (data.result && data.result.content && Array.isArray(data.result.content) && data.result.content.length > 0) {
    try {
      const toolResult = JSON.parse(data.result.content[0].text);
      if (toolResult.success && toolResult.rule) {
        return toolResult.rule;
      }
    } catch {}
  }
  return null;
}

export async function createRule(rule: Partial<Rule>): Promise<Rule | null> {
  const body = {
    jsonrpc: "2.0",
    method: "tools/call",
    params: {
      name: "manage_rule",
      arguments: { action: "create", ...rule }
    },
    id: getRpcId(),
  };
  const res = await fetch(`${API_BASE}`, {
    method: "POST",
    headers: withMcpHeaders(),
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (data.result && data.result.content && Array.isArray(data.result.content) && data.result.content.length > 0) {
    try {
      const toolResult = JSON.parse(data.result.content[0].text);
      if (toolResult.success && toolResult.rule) {
        return toolResult.rule;
      }
    } catch {}
  }
  return null;
}

export async function updateRule(rule_id: string, updates: Partial<Rule>): Promise<Rule | null> {
  const body = {
    jsonrpc: "2.0",
    method: "tools/call",
    params: {
      name: "manage_rule",
      arguments: { action: "update", target: rule_id, ...updates }
    },
    id: getRpcId(),
  };
  const res = await fetch(`${API_BASE}`, {
    method: "POST",
    headers: withMcpHeaders(),
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (data.result && data.result.content && Array.isArray(data.result.content) && data.result.content.length > 0) {
    try {
      const toolResult = JSON.parse(data.result.content[0].text);
      if (toolResult.success && toolResult.rule) {
        return toolResult.rule;
      }
    } catch {}
  }
  return null;
}

export async function deleteRule(rule_id: string): Promise<boolean> {
  const body = {
    jsonrpc: "2.0",
    method: "tools/call",
    params: {
      name: "manage_rule",
      arguments: { action: "delete", target: rule_id }
    },
    id: getRpcId(),
  };
  const res = await fetch(`${API_BASE}`, {
    method: "POST",
    headers: withMcpHeaders(),
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (data.result && data.result.content && Array.isArray(data.result.content) && data.result.content.length > 0) {
    try {
      const toolResult = JSON.parse(data.result.content[0].text);
      if (toolResult.success) {
        return true;
      }
    } catch {}
  }
  return false;
}

export async function validateRule(rule_id: string): Promise<any> {
  const body = {
    jsonrpc: "2.0",
    method: "tools/call",
    params: {
      name: "manage_rule",
      arguments: { action: "validate_rule_hierarchy", target: rule_id }
    },
    id: getRpcId(),
  };
  const res = await fetch(`${API_BASE}`, {
    method: "POST",
    headers: withMcpHeaders(),
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (data.result && data.result.content && Array.isArray(data.result.content) && data.result.content.length > 0) {
    try {
      const toolResult = JSON.parse(data.result.content[0].text);
      if (toolResult.success) {
        return toolResult;
      }
    } catch {}
  }
  return null;
} 