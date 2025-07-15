/**
 * Context Tree Utility Functions
 * Helper functions for hierarchical context tree operations
 */
import { 
  HierarchicalContext, 
  TreeNode, 
  InheritancePath, 
  ContextConflict, 
  ContextSearchFilters,
  SearchResult,
  SearchMatch,
  ContextAnalytics,
  ContextTreeError
} from '../types/context-tree';

export class ContextTreeUtils {
  /**
   * Build hierarchical tree structure from flat context list
   */
  static buildTreeStructure(contexts: HierarchicalContext[]): TreeNode[] {
    const contextMap = new Map<string, HierarchicalContext>();
    const nodeMap = new Map<string, TreeNode>();

    // Create context map for quick lookup
    contexts.forEach(context => {
      contextMap.set(context.context_id, context);
    });

    // Create tree nodes
    contexts.forEach(context => {
      const node: TreeNode = {
        id: context.context_id,
        context,
        level: context.level,
        children: [],
        depth: this.calculateNodeDepth(context.level),
        path: this.calculateNodePath(context, contextMap)
      };
      nodeMap.set(context.context_id, node);
    });

    // Build parent-child relationships
    contexts.forEach(context => {
      const node = nodeMap.get(context.context_id);
      if (!node) return;

      if (context.parent_context_id) {
        const parentNode = nodeMap.get(context.parent_context_id);
        if (parentNode) {
          parentNode.children.push(node);
          node.parent = parentNode;
        }
      }
    });

    // Return root nodes (nodes without parents)
    const rootNodes = Array.from(nodeMap.values()).filter(node => !node.parent);
    
    // Sort by level (global first, then project, then task)
    return rootNodes.sort((a, b) => {
      const levelOrder = { global: 0, project: 1, task: 2 };
      return levelOrder[a.level] - levelOrder[b.level];
    });
  }

  /**
   * Calculate maximum depth of tree
   */
  static calculateMaxDepth(treeNodes: TreeNode[]): number {
    let maxDepth = 0;

    const traverse = (node: TreeNode, depth: number) => {
      maxDepth = Math.max(maxDepth, depth);
      node.children.forEach(child => traverse(child, depth + 1));
    };

    treeNodes.forEach(node => traverse(node, 1));
    return maxDepth;
  }

  /**
   * Calculate node depth based on level
   */
  private static calculateNodeDepth(level: string): number {
    switch (level) {
      case 'global': return 0;
      case 'project': return 1;
      case 'task': return 2;
      default: return 3;
    }
  }

  /**
   * Calculate node path from root to current node
   */
  private static calculateNodePath(
    context: HierarchicalContext, 
    contextMap: Map<string, HierarchicalContext>
  ): string[] {
    const path: string[] = [];
    let current: HierarchicalContext | null = context;

    while (current) {
      path.unshift(current.context_id);
      if (current.parent_context_id) {
        current = contextMap.get(current.parent_context_id) || null;
      } else {
        break;
      }
    }

    return path;
  }

  /**
   * Calculate full inheritance chain for a context
   */
  static calculateInheritancePath(
    contextId: string, 
    contexts: HierarchicalContext[]
  ): InheritancePath {
    const context = contexts.find(c => c.context_id === contextId);
    if (!context) {
      return { path: [], resolved: false, conflicts: [] };
    }

    const path: HierarchicalContext[] = [];
    const conflicts: ContextConflict[] = [];
    let current: HierarchicalContext | null = context;

    // Build inheritance chain from child to parent
    while (current) {
      path.unshift(current);
      
      if (current && current.parent_context_id) {
        const parentId: string = current.parent_context_id;
        current = contexts.find((c): boolean => c.context_id === parentId) || null;
      } else {
        break;
      }
    }

    // Detect conflicts in the inheritance chain
    conflicts.push(...this.detectConflictsInChain(path));

    return {
      path,
      resolved: true,
      conflicts,
      total_resolution_time: performance.now() // Simplified timing
    };
  }

  /**
   * Detect conflicts in inheritance chain
   */
  private static detectConflictsInChain(chain: HierarchicalContext[]): ContextConflict[] {
    const conflicts: ContextConflict[] = [];
    
    if (chain.length < 2) return conflicts;

    const taskContext = chain[chain.length - 1];
    const projectContext = chain.find(c => c.level === 'project');
    const globalContext = chain.find(c => c.level === 'global');

    // Check for property conflicts
    if (taskContext && projectContext) {
      conflicts.push(...this.compareContextData(taskContext, projectContext, 'project'));
    }

    if (taskContext && globalContext) {
      conflicts.push(...this.compareContextData(taskContext, globalContext, 'global'));
    }

    return conflicts;
  }

  /**
   * Compare context data and detect conflicts
   */
  private static compareContextData(
    childContext: HierarchicalContext, 
    parentContext: HierarchicalContext,
    parentLevel: 'project' | 'global'
  ): ContextConflict[] {
    const conflicts: ContextConflict[] = [];
    const childData = childContext.data;
    const parentData = parentContext.data;

    // Check common properties for conflicts
    const commonProps = ['status', 'priority', 'assignees', 'labels'];
    
    commonProps.forEach(prop => {
      if (childData[prop] && parentData[prop] && childData[prop] !== parentData[prop]) {
        conflicts.push({
          field: prop,
          task_value: childData[prop],
          project_value: parentLevel === 'project' ? parentData[prop] : undefined,
          global_value: parentLevel === 'global' ? parentData[prop] : undefined,
          resolution_strategy: 'task_wins', // Task level always wins
          conflict_type: 'value_mismatch'
        });
      }
    });

    return conflicts;
  }

  /**
   * Detect all context conflicts in the tree
   */
  static detectContextConflicts(contexts: HierarchicalContext[]): ContextConflict[] {
    const conflicts: ContextConflict[] = [];
    
    contexts.forEach(context => {
      if (context.level !== 'global') {
        const inheritancePath = this.calculateInheritancePath(context.context_id, contexts);
        conflicts.push(...inheritancePath.conflicts);
      }
    });

    return conflicts;
  }

  /**
   * Filter contexts based on search criteria
   */
  static filterContexts(
    contexts: HierarchicalContext[], 
    filters: ContextSearchFilters
  ): HierarchicalContext[] {
    return contexts.filter(context => {
      // Search term filter
      if (filters.searchTerm) {
        const searchLower = filters.searchTerm.toLowerCase();
        const titleMatch = context.data.title?.toLowerCase().includes(searchLower);
        const descMatch = context.data.description?.toLowerCase().includes(searchLower);
        const idMatch = context.context_id.toLowerCase().includes(searchLower);
        
        if (!titleMatch && !descMatch && !idMatch) {
          return false;
        }
      }

      // Level filter
      if (filters.level !== 'all' && context.level !== filters.level) {
        return false;
      }

      // Status filter
      if (filters.status.length > 0 && !filters.status.includes(context.data.status || '')) {
        return false;
      }

      // Priority filter
      if (filters.priority.length > 0 && !filters.priority.includes(context.data.priority || '')) {
        return false;
      }

      // Assignees filter
      if (filters.assignees.length > 0) {
        const contextAssignees = context.data.assignees || [];
        const hasMatchingAssignee = filters.assignees.some(assignee => 
          contextAssignees.includes(assignee)
        );
        if (!hasMatchingAssignee) {
          return false;
        }
      }

      // Labels filter
      if (filters.labels.length > 0) {
        const contextLabels = context.data.labels || [];
        const hasMatchingLabel = filters.labels.some(label => 
          contextLabels.includes(label)
        );
        if (!hasMatchingLabel) {
          return false;
        }
      }

      return true;
    });
  }

  /**
   * Search contexts with scoring and highlighting
   */
  static searchContexts(
    contexts: HierarchicalContext[], 
    searchTerm: string,
    limit: number = 50
  ): SearchResult[] {
    if (!searchTerm.trim()) return [];

    const results: SearchResult[] = [];
    const searchLower = searchTerm.toLowerCase();

    contexts.forEach(context => {
      const matches: SearchMatch[] = [];
      let score = 0;

      // Search in title
      if (context.data.title) {
        const titleLower = context.data.title.toLowerCase();
        if (titleLower.includes(searchLower)) {
          matches.push({
            field: 'title',
            value: context.data.title,
            highlight: this.highlightText(context.data.title, searchTerm),
            path: ['data', 'title']
          });
          score += titleLower === searchLower ? 100 : 50; // Exact match gets higher score
        }
      }

      // Search in description
      if (context.data.description) {
        const descLower = context.data.description.toLowerCase();
        if (descLower.includes(searchLower)) {
          matches.push({
            field: 'description',
            value: context.data.description,
            highlight: this.highlightText(context.data.description, searchTerm),
            path: ['data', 'description']
          });
          score += 25;
        }
      }

      // Search in context ID
      if (context.context_id.toLowerCase().includes(searchLower)) {
        matches.push({
          field: 'context_id',
          value: context.context_id,
          highlight: this.highlightText(context.context_id, searchTerm),
          path: ['context_id']
        });
        score += 10;
      }

      // Search in labels
      if (context.data.labels) {
        context.data.labels.forEach((label: string) => {
          if (label.toLowerCase().includes(searchLower)) {
            matches.push({
              field: 'labels',
              value: label,
              highlight: this.highlightText(label, searchTerm),
              path: ['data', 'labels']
            });
            score += 15;
          }
        });
      }

      if (matches.length > 0) {
        results.push({ context, matches, score });
      }
    });

    // Sort by score (highest first) and limit results
    return results
      .sort((a, b) => b.score - a.score)
      .slice(0, limit);
  }

  /**
   * Highlight search term in text
   */
  private static highlightText(text: string, searchTerm: string): string {
    const regex = new RegExp(`(${searchTerm})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
  }

  /**
   * Calculate context analytics
   */
  static calculateAnalytics(contexts: HierarchicalContext[]): ContextAnalytics {
    const analytics: ContextAnalytics = {
      total_contexts: contexts.length,
      contexts_by_level: {
        global: 0,
        project: 0,
        task: 0
      },
      health_distribution: {
        healthy: 0,
        warning: 0,
        error: 0,
        stale: 0
      },
      inheritance_depth_avg: 0,
      resolution_time_avg: 0,
      conflicts_count: 0,
      delegation_requests: 0
    };

    // Count contexts by level
    contexts.forEach(context => {
      analytics.contexts_by_level[context.level]++;
    });

    // Calculate inheritance depth average
    const depths = contexts.map(context => {
      const path = this.calculateInheritancePath(context.context_id, contexts);
      return path.path.length;
    });
    analytics.inheritance_depth_avg = depths.length > 0 
      ? depths.reduce((sum, depth) => sum + depth, 0) / depths.length 
      : 0;

    // Count conflicts
    analytics.conflicts_count = this.detectContextConflicts(contexts).length;

    return analytics;
  }

  /**
   * Validate tree structure integrity
   */
  static validateTreeStructure(contexts: HierarchicalContext[]): ContextTreeError[] {
    const errors: ContextTreeError[] = [];
    const contextIds = new Set(contexts.map(c => c.context_id));

    contexts.forEach(context => {
      // Check for orphaned contexts (parent doesn't exist)
      if (context.parent_context_id && !contextIds.has(context.parent_context_id)) {
        errors.push({
          code: 'ORPHANED_CONTEXT',
          message: `Context ${context.context_id} references non-existent parent ${context.parent_context_id}`,
          context_id: context.context_id,
          level: context.level,
          operation: 'validate_structure',
          timestamp: Date.now()
        });
      }

      // Check for circular references
      if (this.hasCircularReference(context, contexts)) {
        errors.push({
          code: 'CIRCULAR_REFERENCE',
          message: `Context ${context.context_id} has circular reference in inheritance chain`,
          context_id: context.context_id,
          level: context.level,
          operation: 'validate_structure',
          timestamp: Date.now()
        });
      }

      // Check for invalid level hierarchy
      if (context.parent_context_id) {
        const parent = contexts.find(c => c.context_id === context.parent_context_id);
        if (parent && !this.isValidLevelHierarchy(context.level, parent.level)) {
          errors.push({
            code: 'INVALID_HIERARCHY',
            message: `Invalid hierarchy: ${context.level} cannot inherit from ${parent.level}`,
            context_id: context.context_id,
            level: context.level,
            operation: 'validate_structure',
            timestamp: Date.now()
          });
        }
      }
    });

    return errors;
  }

  /**
   * Check for circular references in inheritance chain
   */
  private static hasCircularReference(
    context: HierarchicalContext, 
    contexts: HierarchicalContext[]
  ): boolean {
    const visited = new Set<string>();
    let current: HierarchicalContext | null = context;

    while (current && current.parent_context_id) {
      if (visited.has(current.context_id)) {
        return true; // Circular reference detected
      }
      visited.add(current.context_id);
      current = contexts.find(c => c.context_id === current?.parent_context_id) || null;
    }

    return false;
  }

  /**
   * Validate level hierarchy rules
   */
  private static isValidLevelHierarchy(childLevel: string, parentLevel: string): boolean {
    const validHierarchies: Record<string, string[]> = {
      task: ['project', 'global'],
      project: ['global'],
      global: []
    };

    return validHierarchies[childLevel]?.includes(parentLevel) || false;
  }

  /**
   * Get context by ID with error handling
   */
  static getContextById(
    contexts: HierarchicalContext[], 
    contextId: string
  ): HierarchicalContext | null {
    return contexts.find(c => c.context_id === contextId) || null;
  }

  /**
   * Get all descendants of a context
   */
  static getDescendants(
    contextId: string, 
    contexts: HierarchicalContext[]
  ): HierarchicalContext[] {
    const descendants: HierarchicalContext[] = [];
    const queue = [contextId];

    while (queue.length > 0) {
      const currentId = queue.shift()!;
      const children = contexts.filter(c => c.parent_context_id === currentId);
      
      children.forEach(child => {
        descendants.push(child);
        queue.push(child.context_id);
      });
    }

    return descendants;
  }

  /**
   * Get all ancestors of a context
   */
  static getAncestors(
    contextId: string, 
    contexts: HierarchicalContext[]
  ): HierarchicalContext[] {
    const ancestors: HierarchicalContext[] = [];
    let current = contexts.find(c => c.context_id === contextId);

    while (current && current.parent_context_id) {
      const parent = contexts.find(c => c.context_id === current!.parent_context_id);
      if (parent) {
        ancestors.unshift(parent);
        current = parent;
      } else {
        break;
      }
    }

    return ancestors;
  }

  /**
   * Export tree structure to JSON
   */
  static exportTreeStructure(treeNodes: TreeNode[]): string {
    const exportData = {
      exported_at: new Date().toISOString(),
      tree_structure: treeNodes,
      metadata: {
        node_count: this.countAllNodes(treeNodes),
        max_depth: this.calculateMaxDepth(treeNodes),
        levels: this.getLevelDistribution(treeNodes)
      }
    };

    return JSON.stringify(exportData, null, 2);
  }

  /**
   * Count all nodes in tree (including children)
   */
  private static countAllNodes(treeNodes: TreeNode[]): number {
    let count = 0;
    
    const traverse = (node: TreeNode) => {
      count++;
      node.children.forEach(child => traverse(child));
    };

    treeNodes.forEach(node => traverse(node));
    return count;
  }

  /**
   * Get distribution of contexts by level
   */
  private static getLevelDistribution(treeNodes: TreeNode[]): Record<string, number> {
    const distribution = { global: 0, project: 0, task: 0 };
    
    const traverse = (node: TreeNode) => {
      distribution[node.level]++;
      node.children.forEach(child => traverse(child));
    };

    treeNodes.forEach(node => traverse(node));
    return distribution;
  }
}