import React from 'react';
import GraphView from '../components/GraphView';
import { motion } from 'framer-motion';

export default function MarketingScreenshot() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex-1 flex flex-col h-full bg-[#050505]"
    >
      <div className="flex-1 w-full h-full relative">
        <GraphView tasks={[]} manifest={null} analytics={[]} />
      </div>
    </motion.div>
  );
}
