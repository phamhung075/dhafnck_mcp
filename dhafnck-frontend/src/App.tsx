import React from 'react';
import './App.css';
import './styles/globals.css';
import './styles/accessibility.css';
import { MainApplication } from './components/MainApplication';
// import SimpleApp from './SimpleApp';
import { AccessibilityProvider, SkipLinks } from './utils/AccessibilityUtils';
import { EnhancedErrorBoundary, setupGlobalErrorHandling } from './components/common/EnhancedErrorBoundary';

// Setup global error handling
setupGlobalErrorHandling();

function App() {
  return (
    <EnhancedErrorBoundary enableReporting={true} maxRetries={3}>
      <AccessibilityProvider>
        <div className="min-h-screen bg-gray-50">
          {/* Skip Links for Keyboard Navigation */}
          <SkipLinks links={[
            { href: '#main-content', text: 'Skip to main content' },
            { href: '#primary-navigation', text: 'Skip to navigation' },
            { href: '#search', text: 'Skip to search' }
          ]} />
          
          {/* Main Application */}
          <div id="main-content" role="main">
            <MainApplication
              initialAgent="@uber_orchestrator_agent"
              initialProject={undefined}
            />
          </div>
        </div>
      </AccessibilityProvider>
    </EnhancedErrorBoundary>
  );
}

export default App;

