import React from 'react';
import GraphView from '../components/GraphView';
import { motion } from 'framer-motion';
import { MOCK_COMPLEX_TASKS, MOCK_COMPLEX_ANALYTICS } from '../mockData';

export default function MarketingComplexGraph() {
  return (
    <div
      className="w-full h-[800px] bg-[#000] relative rounded-2xl border border-white/10 overflow-hidden"
    >
      <GraphView 
        tasks={MOCK_COMPLEX_TASKS} 
        manifest={null} 
        analytics={MOCK_COMPLEX_ANALYTICS} 
      />
    </div>
  );
}
