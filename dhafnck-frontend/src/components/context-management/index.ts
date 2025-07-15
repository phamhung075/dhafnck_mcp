/**
 * Context Management Components Export
 * All components from Prompt 3B: Context Delegation & Management
 */

// Main components
export { ContextDetailsPanel } from '../ContextDetailsPanel';
export { ContextDataEditor } from '../ContextDataEditor';
export { ContextDelegationWorkflow } from '../ContextDelegationWorkflow';
export { DelegationQueueViewer } from '../DelegationQueueViewer';
export { ContextInheritanceDebugger } from '../ContextInheritanceDebugger';

// Supporting components
export { ContextInsightsManager } from '../ContextInsightsManager';
export { ContextInheritanceView } from '../ContextInheritanceView';
export { ContextProgressView } from '../ContextProgressView';
export { ContextNextStepsEditor } from '../ContextNextStepsEditor';

// Hooks
export { useContextManagement } from '../../hooks/useContextManagement';

// Types
export * from '../../types/context-delegation';

// Demo component
export { ContextManagementDemo } from '../ContextManagementDemo';

// Integration usage example
/*
import {
  ContextDetailsPanel,
  ContextDelegationWorkflow,
  DelegationQueueViewer,
  ContextInheritanceDebugger,
  useContextManagement,
  type ContextDetailsPanelProps,
  type DelegationRequest
} from './components/context-management';

function MyContextApp() {
  const { state, actions } = useContextManagement('project-1', 'task-1');
  
  return (
    <div>
      <ContextDetailsPanel
        context={state.selectedContext}
        resolvedContext={state.resolvedContext}
        inheritanceChain={state.inheritanceChain}
        onUpdateContext={actions.updateContext}
        onAddInsight={actions.addInsight}
        onAddProgress={actions.addProgress}
        onUpdateNextSteps={actions.updateNextSteps}
        onForceRefresh={() => actions.refreshContext('task-1')}
      />
    </div>
  );
}
*/