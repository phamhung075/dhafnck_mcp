import React from "react";
import { Badge } from "./ui/badge";
import { Task } from "../api";

interface ClickableAssigneesProps {
  assignees: string[];
  task: Task;
  onAgentClick: (agentName: string, task: Task) => void;
  variant?: "default" | "secondary" | "destructive" | "outline";
  className?: string;
  showAsString?: boolean; // Option to show as comma-separated string instead of badges
}

export const ClickableAssignees: React.FC<ClickableAssigneesProps> = ({
  assignees,
  task,
  onAgentClick,
  variant = "secondary",
  className = "",
  showAsString = false
}) => {
  if (!assignees || assignees.length === 0) {
    return <span className="text-sm text-muted-foreground">Unassigned</span>;
  }

  if (showAsString) {
    // Show as clickable text (for backward compatibility)
    return (
      <span className="text-sm font-medium">
        {assignees.map((assignee, index) => (
          <React.Fragment key={index}>
            <span
              className="cursor-pointer hover:text-primary underline decoration-dotted"
              onClick={() => onAgentClick(assignee, task)}
              title={`Click to call ${assignee}`}
            >
              {assignee}
            </span>
            {index < assignees.length - 1 && ", "}
          </React.Fragment>
        ))}
      </span>
    );
  }

  // Show as clickable badges
  return (
    <div className={`flex flex-wrap gap-1 ${className}`}>
      {assignees.map((assignee: string, index: number) => (
        <Badge
          key={index}
          variant={variant}
          className="px-2 cursor-pointer hover:bg-primary hover:text-primary-foreground transition-colors"
          onClick={() => onAgentClick(assignee, task)}
          title={`Click to call ${assignee}`}
        >
          {assignee}
        </Badge>
      ))}
    </div>
  );
};

export default ClickableAssignees;