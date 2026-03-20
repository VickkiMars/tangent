import React from 'react';
import { useSearchParams } from 'react-router-dom';
import TaskBoard from '../components/TaskBoard';

const Workspace = () => {
  const [searchParams] = useSearchParams();
  const taskId = searchParams.get('taskId');

  // Workspace defaults to the latest running or last completed task.
  // In our mock data, 'tkt_89123_data_export' is running.
  // Or 'tkt_12345_customer_refund' is active (which might mean running in some contexts, but let's stick to the prompt's "running" status).
  // The prompt description uses 'tkt_12345_customer_refund' as the example for the center column.
  
  return (
    <div className="-mx-4 sm:-mx-6 h-[calc(100dvh-5rem)] sm:h-[calc(100dvh-7rem)] md:h-[calc(100vh-8rem)] overflow-hidden">
      <TaskBoard defaultTaskId={taskId} />
    </div>
  );
};

export default Workspace;
