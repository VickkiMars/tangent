import React from 'react';
import TaskBoard from '../components/TaskBoard';

const TaskView = () => {
  return (
    <div className="-mx-4 sm:-mx-6 h-[calc(100dvh-5rem)] sm:h-[calc(100dvh-7rem)] md:h-[calc(100vh-8rem)] overflow-hidden">
      <TaskBoard />
    </div>
  );
};

export default TaskView;
