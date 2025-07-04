# Claude Code Project Configuration
User Identification:
   - You should assume that you are interacting with default_user
   - If you have not identified default_user, proactively try to do so.

You are the AI used within the AI editor Cursor, so you can view, edit, create, and run files within the project directory. If you are asked to identify the cause of a bug, fix a bug, edit a file, or create a file, please execute the following function. Please do not ask me (human) to give you a file or ask you to create a file, but you (AI) can do it by executing the following functions. If an error occurs and you are unable to execute the function, please consult with us.

edit_file: Edit an existing file, create a new file
read_file: Read the contents of a file
grep_search: Search in the codebase based on a specific creator
list_dir: Get a list of files and folders in a specific directory”

- ALWAYS edit file in small chunks
- ALWAYS read `.cursor/rules/dhafnck_mcp.mdc` first
- ALWAYS use sequential-thinking mcp for complex request or tasks
- ALWAYS ask default_user before creating new files

- Use memory MCP to store only globally important default_user requests, or to store what the default_user specifically asks the AI to remember.

- Fix root causes, not symptoms

- Detailed summaries without missing important details

- AI files config, rules in .cursor/rules/

- No root directory file creation without permission

- Respect project structure unless changes requested

- Monitor for requests that would exceed Pro plan token limits

- If a request would require paid usage beyond Pro limits, AI MUST immediately terminate the chat and inform default_user to start a new chat

---

when open claude:
- read `/home/<username>/agentic-project/.cursor/rules/dhafnck_mcp.mdc`
- read `/home/<username>/agentic-project/.cursor/rules/agents.mdc`
- read `/home/<username>/agentic-project/.cursor/rules/memory.mdc`
- read `.cursor/rules/need-update-this-file-if-change-project-tree.mdc`

when get_task() or next_task() : read `.cursor/rules/auto_rule.mdc`

when change project or change git branch: update .cursor/rules/need-update-this-file-if-change-project-tree.mdc