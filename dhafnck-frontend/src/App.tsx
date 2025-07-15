import { useState } from 'react';
import './App.css';
import ProjectList from './components/ProjectList';
import TaskList from './components/TaskList';

function App() {
  const [selection, setSelection] = useState<{ projectId: string, branchId: string } | null>(null);

  return (
    <div className="flex h-screen bg-background text-foreground">
      <aside className="w-1/4 min-w-[300px] max-w-[400px] border-r p-4 overflow-y-auto">
        <ProjectList onSelect={(projectId: string, branchId: string) => setSelection({ projectId, branchId })} />
      </aside>
      <main className="flex-1 flex flex-col p-4">
        <div className="flex-1 overflow-y-auto">
          {selection ? (
            <TaskList key={`${selection.projectId}-${selection.branchId}`} projectId={selection.projectId} taskTreeId={selection.branchId} />
          ) : (
            <div className="text-center text-muted-foreground mt-10">Select a project and branch to see tasks.</div>
          )}
        </div>
      </main>
    </div>
  )
}

export default App;

