import { motion } from 'framer-motion';
import { CheckCircle, XCircle, ChevronRight, Activity, Calendar } from 'lucide-react';

const History = () => {
  const historyItems = [
    {
      id: 'task-1290',
      task: 'Real-time data synchronization with legacy database',
      date: 'Feb 21, 2026',
      status: 'running',
      agents: 4,
      duration: '5m 12s',
      cost: '$0.003'
    },
    {
      id: 'task-1289',
      task: 'Analyze competitor pricing models for Q1 2026',
      date: 'Feb 20, 2026',
      status: 'completed',
      agents: 3,
      duration: '4m 12s',
      cost: '$0.42'
    },
    {
      id: 'task-1288',
      task: 'Generate and deploy landing page for "Project Alpha"',
      date: 'Feb 19, 2026',
      status: 'completed',
      agents: 5,
      duration: '12m 45s',
      cost: '$1.20'
    },
    {
      id: 'task-1287',
      task: 'Scrape Twitter for sentiment analysis on "AI Regulations"',
      date: 'Feb 18, 2026',
      status: 'failed',
      agents: 2,
      duration: '1m 30s',
      cost: '$0.05'
    },
    {
      id: 'task-1286',
      task: 'Automate weekly report generation from Salesforce',
      date: 'Feb 15, 2026',
      status: 'completed',
      agents: 1,
      duration: '45s',
      cost: '$0.08'
    },
    {
      id: 'task-1285',
      task: 'Research potential leads in the fintech sector',
      date: 'Feb 10, 2026',
      status: 'completed',
      agents: 4,
      duration: '8m 20s',
      cost: '$0.95'
    }
  ];

  const StatusBadge = ({ status }) => (
    <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border flex-shrink-0 ${
      status === 'completed'
        ? 'bg-success/10 text-success border-success/20'
        : status === 'running'
        ? 'bg-blue-500/10 text-blue-500 border-blue-500/20'
        : 'bg-red-500/10 text-red-500 border-red-500/20'
    }`}>
      {status === 'completed' ? <CheckCircle size={10} /> :
       status === 'running' ? <Activity size={10} className="animate-pulse" /> :
       <XCircle size={10} />}
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </div>
  );

  return (
    <div className="min-h-screen pb-20 max-w-7xl mx-auto">
      {/* Page header */}
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-end mb-8 sm:mb-10 gap-4">
        <div>
          <h1 className="text-3xl sm:text-4xl font-bold mb-2 text-white">Task History</h1>
          <p className="text-text-secondary text-sm sm:text-base">
            Archive of all ephemeral agent deployments and their results.
          </p>
        </div>
        <div className="flex gap-3 sm:gap-4">
          <div className="glass-panel px-4 py-2 rounded-lg flex flex-col items-center">
            <span className="text-xs text-text-tertiary uppercase tracking-wider">Total Tasks</span>
            <span className="text-xl font-bold text-white">1,248</span>
          </div>
          <div className="glass-panel px-4 py-2 rounded-lg flex flex-col items-center">
            <span className="text-xs text-text-tertiary uppercase tracking-wider">Success Rate</span>
            <span className="text-xl font-bold text-success">98.4%</span>
          </div>
        </div>
      </div>

      <div className="glass-panel rounded-2xl overflow-hidden border border-white/10">
        {/* Desktop table header — hidden on mobile */}
        <div className="hidden sm:grid grid-cols-12 gap-4 p-4 border-b border-white/10 bg-black/20 text-xs font-bold text-text-tertiary uppercase tracking-wider">
          <div className="col-span-5">Task Description</div>
          <div className="col-span-2">Status</div>
          <div className="col-span-2">Date</div>
          <div className="col-span-1">Agents</div>
          <div className="col-span-1">Duration</div>
          <div className="col-span-1 text-right">Action</div>
        </div>

        <div className="divide-y divide-white/5">
          {historyItems.map((item, index) => (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              key={item.id}
              className="hover:bg-white/5 transition-colors group cursor-pointer"
            >
              {/* Mobile card layout */}
              <div className="sm:hidden p-4 flex flex-col gap-2.5">
                <div className="flex items-center justify-between gap-2">
                  <StatusBadge status={item.status} />
                  <button className="p-1.5 rounded-lg hover:bg-white/10 text-text-tertiary hover:text-white transition-colors">
                    <ChevronRight size={15} />
                  </button>
                </div>
                <p className="font-medium text-white leading-snug text-sm">{item.task}</p>
                <p className="text-xs text-text-tertiary font-mono">{item.id}</p>
                <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-text-secondary">
                  <span className="flex items-center gap-1">
                    <Calendar size={10} className="text-text-tertiary" />{item.date}
                  </span>
                  <span>{item.agents} agents</span>
                  <span className="font-mono">{item.duration}</span>
                  <span>{item.cost}</span>
                </div>
              </div>

              {/* Desktop table row */}
              <div className="hidden sm:grid grid-cols-12 gap-4 p-4 items-center">
                <div className="col-span-5">
                  <div className="font-medium text-white group-hover:text-primary-light transition-colors truncate">
                    {item.task}
                  </div>
                  <div className="text-xs text-text-tertiary font-mono mt-1">{item.id}</div>
                </div>

                <div className="col-span-2">
                  <StatusBadge status={item.status} />
                </div>

                <div className="col-span-2 text-sm text-text-secondary flex items-center gap-2">
                  <Calendar size={12} className="text-text-tertiary"/>
                  {item.date}
                </div>

                <div className="col-span-1 text-sm text-text-secondary">
                  {item.agents}
                </div>

                <div className="col-span-1 text-sm text-text-secondary font-mono">
                  {item.duration}
                </div>

                <div className="col-span-1 text-right">
                  <button className="p-2 rounded-lg hover:bg-white/10 text-text-tertiary hover:text-white transition-colors">
                    <ChevronRight size={16} />
                  </button>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      <div className="mt-8 flex justify-center">
        <button className="btn-secondary text-sm">Load More History</button>
      </div>
    </div>
  );
};

export default History;
