import React from "react";
import { formatContextDisplay } from "../utils/contextHelpers";

/**
 * Test component to verify the new context structure handling
 * Shows how completion_summary data is displayed in both new and legacy formats
 */
export const ContextStructureTest: React.FC = () => {
  // Test data - New format (current_session_summary)
  const newFormatContext = {
    data: {
      progress: {
        current_session_summary: "Task completed successfully. Implemented user authentication with JWT tokens, added password validation, and created comprehensive unit tests. All acceptance criteria met.",
        completion_percentage: 100,
        next_steps: [
          "Performed unit tests for authentication service",
          "Manual testing of login/logout flows", 
          "Verified token expiry handling",
          "Tested edge cases for invalid credentials"
        ],
        completed_actions: [
          "Implemented JWT service",
          "Created login/logout endpoints",
          "Added password hashing"
        ]
      },
      metadata: {
        status: "done"
      }
    }
  };

  // Test data - Legacy format (completion_summary)
  const legacyFormatContext = {
    data: {
      progress: {
        completion_summary: "Legacy task completion. Implemented user registration feature with email validation and database integration.",
        completion_percentage: 100,
        next_steps: [
          "Tested registration form",
          "Verified email validation",
          "Checked database persistence"
        ]
      },
      metadata: {
        status: "completed"
      }
    }
  };

  // Test data - Mixed/No completion info
  const noCompletionContext = {
    data: {
      progress: {
        completion_percentage: 50
      },
      metadata: {
        status: "in_progress"
      }
    }
  };

  const newDisplay = formatContextDisplay(newFormatContext.data);
  const legacyDisplay = formatContextDisplay(legacyFormatContext.data);
  const noCompletionDisplay = formatContextDisplay(noCompletionContext.data);

  return (
    <div className="p-6 space-y-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Context Structure Test Page</h1>
      <p className="text-muted-foreground mb-6">
        This page tests the new context structure handling for completion_summary data.
        It shows how the frontend now supports both new (progress.current_session_summary) 
        and legacy (progress.completion_summary) formats.
      </p>

      {/* New Format Test */}
      <div className="border rounded-lg p-4">
        <h2 className="text-lg font-semibold mb-4 text-green-700">New Format Test (progress.current_session_summary)</h2>
        
        {newDisplay.completionSummary && (
          <div className="mb-4">
            <h4 className="font-semibold text-sm mb-2 text-green-700">
              Completion Summary{newDisplay.isLegacy ? ' (Legacy Format)' : ''}
            </h4>
            <div className={`p-3 rounded ${newDisplay.isLegacy ? 'bg-yellow-50' : 'bg-green-50'}`}>
              <p className="text-sm whitespace-pre-wrap">{newDisplay.completionSummary}</p>
              {newDisplay.completionPercentage && (
                <div className="mt-2 pt-2 border-t border-green-200">
                  <span className="text-xs text-muted-foreground">Completion: </span>
                  <span className="text-xs font-medium">{newDisplay.completionPercentage}%</span>
                </div>
              )}
              {newDisplay.isLegacy && (
                <p className="text-xs text-muted-foreground mt-2 italic">
                  Note: This is using the legacy completion_summary format
                </p>
              )}
            </div>
          </div>
        )}

        {newDisplay.taskStatus && (
          <div className="mb-4">
            <h4 className="font-semibold text-sm mb-2 text-blue-700">Task Status</h4>
            <div className="bg-blue-50 p-3 rounded">
              <span className="inline-block px-2 py-1 bg-blue-200 text-blue-800 text-xs font-medium rounded">
                {newDisplay.taskStatus}
              </span>
            </div>
          </div>
        )}

        {newDisplay.testingNotes.length > 0 && (
          <div className="mb-4">
            <h4 className="font-semibold text-sm mb-2 text-purple-700">Testing Notes & Next Steps</h4>
            <div className="bg-purple-50 p-3 rounded space-y-2">
              {newDisplay.testingNotes.map((step: string, index: number) => (
                <div key={index} className="border-l-4 border-purple-300 pl-3">
                  <p className="text-sm">{step}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="text-xs text-muted-foreground">
          <strong>Format Detection:</strong> {newDisplay.isLegacy ? 'Legacy' : 'New'} | 
          <strong> Has Info:</strong> {newDisplay.hasInfo ? 'Yes' : 'No'}
        </div>
      </div>

      {/* Legacy Format Test */}
      <div className="border rounded-lg p-4">
        <h2 className="text-lg font-semibold mb-4 text-yellow-700">Legacy Format Test (progress.completion_summary)</h2>
        
        {legacyDisplay.completionSummary && (
          <div className="mb-4">
            <h4 className="font-semibold text-sm mb-2 text-green-700">
              Completion Summary{legacyDisplay.isLegacy ? ' (Legacy Format)' : ''}
            </h4>
            <div className={`p-3 rounded ${legacyDisplay.isLegacy ? 'bg-yellow-50' : 'bg-green-50'}`}>
              <p className="text-sm whitespace-pre-wrap">{legacyDisplay.completionSummary}</p>
              {legacyDisplay.completionPercentage && (
                <div className="mt-2 pt-2 border-t border-green-200">
                  <span className="text-xs text-muted-foreground">Completion: </span>
                  <span className="text-xs font-medium">{legacyDisplay.completionPercentage}%</span>
                </div>
              )}
              {legacyDisplay.isLegacy && (
                <p className="text-xs text-muted-foreground mt-2 italic">
                  Note: This is using the legacy completion_summary format
                </p>
              )}
            </div>
          </div>
        )}

        {legacyDisplay.taskStatus && (
          <div className="mb-4">
            <h4 className="font-semibold text-sm mb-2 text-blue-700">Task Status</h4>
            <div className="bg-blue-50 p-3 rounded">
              <span className="inline-block px-2 py-1 bg-blue-200 text-blue-800 text-xs font-medium rounded">
                {legacyDisplay.taskStatus}
              </span>
            </div>
          </div>
        )}

        {legacyDisplay.testingNotes.length > 0 && (
          <div className="mb-4">
            <h4 className="font-semibold text-sm mb-2 text-purple-700">Testing Notes & Next Steps</h4>
            <div className="bg-purple-50 p-3 rounded space-y-2">
              {legacyDisplay.testingNotes.map((step: string, index: number) => (
                <div key={index} className="border-l-4 border-purple-300 pl-3">
                  <p className="text-sm">{step}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="text-xs text-muted-foreground">
          <strong>Format Detection:</strong> {legacyDisplay.isLegacy ? 'Legacy' : 'New'} | 
          <strong> Has Info:</strong> {legacyDisplay.hasInfo ? 'Yes' : 'No'}
        </div>
      </div>

      {/* No Completion Info Test */}
      <div className="border rounded-lg p-4">
        <h2 className="text-lg font-semibold mb-4 text-gray-700">No Completion Info Test</h2>
        
        {!noCompletionDisplay.hasInfo && (
          <div className="bg-gray-50 p-3 rounded text-center">
            <p className="text-sm text-muted-foreground">No completion information available</p>
          </div>
        )}

        {noCompletionDisplay.taskStatus && (
          <div className="mb-4">
            <h4 className="font-semibold text-sm mb-2 text-blue-700">Task Status</h4>
            <div className="bg-blue-50 p-3 rounded">
              <span className="inline-block px-2 py-1 bg-blue-200 text-blue-800 text-xs font-medium rounded">
                {noCompletionDisplay.taskStatus}
              </span>
            </div>
          </div>
        )}

        <div className="text-xs text-muted-foreground">
          <strong>Format Detection:</strong> {noCompletionDisplay.isLegacy ? 'Legacy' : 'New'} | 
          <strong> Has Info:</strong> {noCompletionDisplay.hasInfo ? 'Yes' : 'No'}
        </div>
      </div>

      {/* Raw Data Display */}
      <div className="border rounded-lg p-4">
        <h2 className="text-lg font-semibold mb-4">Raw Test Data</h2>
        <div className="space-y-4">
          <div>
            <h3 className="font-medium text-sm mb-2">New Format Context:</h3>
            <pre className="text-xs bg-gray-100 p-2 rounded overflow-x-auto">
              {JSON.stringify(newFormatContext, null, 2)}
            </pre>
          </div>
          <div>
            <h3 className="font-medium text-sm mb-2">Legacy Format Context:</h3>
            <pre className="text-xs bg-gray-100 p-2 rounded overflow-x-auto">
              {JSON.stringify(legacyFormatContext, null, 2)}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ContextStructureTest;