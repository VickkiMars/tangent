import React from 'react';
import TaskBoard from '../components/TaskBoard';

const Workspace = () => {
  // Workspace defaults to the latest running or last completed task.
  // In our mock data, 'tkt_89123_data_export' is running.
  // Or 'tkt_12345_customer_refund' is active (which might mean running in some contexts, but let's stick to the prompt's "running" status).
  // The prompt description uses 'tkt_12345_customer_refund' as the example for the center column.
  
  return (
    <div className="pt-20 px-6 h-screen overflow-hidden">
      <TaskBoard defaultTaskId="tkt_12345_customer_refund" />
    </div>
  );
};

export default Workspace;
