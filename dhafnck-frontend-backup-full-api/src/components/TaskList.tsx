import { Minus, Pencil, Plus, Trash2 } from "lucide-react";
import React, { useEffect, useState } from "react";
import { listTasks, Task } from "../api";
import { SubtaskList } from "./SubtaskList";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./ui/table";

interface TaskListProps {
  projectId: string;
  taskTreeId: string;
}

const TaskList: React.FC<TaskListProps> = ({ projectId, taskTreeId }) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedTasks, setExpandedTasks] = useState<Record<string, boolean>>({});

  useEffect(() => {
    setLoading(true);
    listTasks({ git_branch_id: taskTreeId })
      .then(setTasks)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [projectId, taskTreeId]);

  const toggleTaskExpansion = (taskId: string) => {
    setExpandedTasks(prev => ({ ...prev, [taskId]: !prev[taskId] }));
  };

  if (loading) return <div>Loading tasks...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead style={{ width: '50px' }}></TableHead>
          <TableHead>Title</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Priority</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {tasks.map(task => (
          <React.Fragment key={task.id}>
            <TableRow>
              <TableCell>
                <Button variant="ghost" size="icon" onClick={() => toggleTaskExpansion(task.id)}>
                  {expandedTasks[task.id] ? <Minus /> : <Plus />}
                </Button>
              </TableCell>
              <TableCell>{task.title}</TableCell>
              <TableCell>
                <Badge>{task.status}</Badge>
              </TableCell>
              <TableCell>
                <Badge variant="secondary">{task.priority}</Badge>
              </TableCell>
              <TableCell>
                <Button variant="ghost" size="icon">
                  <Pencil />
                </Button>
                <Button variant="ghost" size="icon">
                  <Trash2 />
                </Button>
              </TableCell>
            </TableRow>
            {expandedTasks[task.id] && (
              <TableRow>
                <TableCell colSpan={5}>
                  <SubtaskList
                    key={task.id} // Ensures re-mount on task change
                    projectId={projectId}
                    taskTreeId={taskTreeId}
                    parentTaskId={task.id}
                  />
                </TableCell>
              </TableRow>
            )}
          </React.Fragment>
        ))}
      </TableBody>
    </Table>
  );
};

export default TaskList; 