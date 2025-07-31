# Frontend Changelog

## 2025-01-18

### Changed
- Updated Task interface to use subtask IDs (string[]) instead of full Subtask objects
- Modified TaskList component to show subtask count with "subtasks" label
- Updated TaskDetailsDialog to display subtask IDs with note to view full details in Subtasks tab
- Aligned frontend with new backend architecture where Task entities only store subtask IDs

### Technical Details
- Task.subtasks is now string[] (array of UUIDs) instead of Subtask[]
- SubtaskList component continues to fetch full subtask details using listSubtasks API
- No breaking changes for end users - subtask functionality remains the same