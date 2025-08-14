import { useState, useEffect } from 'react';
import './App.css';
import ProjectList from './components/ProjectList';
import TaskList from './components/TaskList';
import { Button } from './components/ui/button';
import { Menu, X } from 'lucide-react';

function App() {
  const [selection, setSelection] = useState<{ projectId: string, branchId: string } | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isLargeScreen, setIsLargeScreen] = useState(false);
  const [projectListRefreshKey, setProjectListRefreshKey] = useState(0);

  // Initialize sidebar state based on screen size
  useEffect(() => {
    const handleResize = () => {
      const large = window.innerWidth >= 1024;
      setIsLargeScreen(large);
      // Only auto-open on large screens
      if (large) {
        setSidebarOpen(true);
      }
    };

    // Set initial state
    handleResize();

    // Add event listener
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <div className="flex flex-col h-screen bg-background text-foreground">
      {/* Header */}
      <header className="border-b bg-white dark:bg-gray-900 px-4 py-3 shadow-sm">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">DhafnckMCP</h1>
          <span className="text-sm text-gray-500 dark:text-gray-400">Multi-Project AI Orchestration Platform</span>
        </div>
      </header>
      
      {/* Main content area */}
      <div className="flex flex-1 relative overflow-hidden">
        {/* Sidebar */}
        <aside className={`
        fixed lg:static
        ${sidebarOpen ? 'left-0' : '-left-full'}
        w-96 lg:w-1/3 lg:min-w-[400px] lg:max-w-[500px]
        h-full
        border-r p-4 overflow-y-auto
        bg-white dark:bg-gray-900
        transition-all duration-300 ease-in-out
        z-20
        lg:translate-x-0
        shadow-lg lg:shadow-none
      `}>
        <ProjectList 
          refreshKey={projectListRefreshKey}
          onSelect={(projectId: string, branchId: string) => {
            setSelection({ projectId, branchId });
            // Auto-close sidebar on mobile after selection
            if (!isLargeScreen) {
              setSidebarOpen(false);
            }
          }} />
      </aside>

      {/* Mobile overlay */}
      {sidebarOpen && !isLargeScreen && (
        <div 
          className="fixed inset-0 bg-black/50 z-10 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Toggle button for mobile */}
      {!isLargeScreen && (
        <Button
          variant="outline"
          size="icon"
          className={`fixed z-30 lg:hidden bg-white dark:bg-gray-800 border-2 shadow-lg hover:shadow-xl ${
            sidebarOpen ? 'top-4 right-4' : 'top-4 left-4'
          }`}
          onClick={() => setSidebarOpen(!sidebarOpen)}
        >
          {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </Button>
      )}

        {/* Main content */}
        <main className="flex-1 flex flex-col p-4 w-full">
          {/* Add padding top on mobile to account for menu button */}
          <div className="flex-1 overflow-y-auto pt-12 lg:pt-0">
            {selection ? (
              <TaskList 
              key={`${selection.projectId}-${selection.branchId}`} 
              projectId={selection.projectId} 
              taskTreeId={selection.branchId} 
              onTasksChanged={() => {
                console.log('App: onTasksChanged called, incrementing refreshKey');
                setProjectListRefreshKey(prev => prev + 1);
              }}
            />
            ) : (
              <div className="text-center text-muted-foreground mt-10">Select a project and branch to see tasks.</div>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}

export default App;

