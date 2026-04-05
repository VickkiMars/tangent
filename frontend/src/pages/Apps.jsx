import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Box, Play, Trash2, Calendar, HardDrive, RefreshCw } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const Apps = () => {
  const [apps, setApps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const fetchApps = async () => {
    setLoading(true);
    try {
      // We will point to the REST API /apps
      const token = localStorage.getItem('token');
      // Adjust API_BASE to your env, defaulting to local
      const res = await fetch('http://localhost:8000/apps', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!res.ok) throw new Error('Failed to fetch apps');
      const data = await res.json();
      setApps(data);
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApps();
  }, []);

  const handleDeploy = async (appId) => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`http://localhost:8000/apps/${appId}/run`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          provider: 'google',
          model: 'gemini-3.1-flash-lite-preview'
        })
      });
      
      if (!res.ok) throw new Error('Failed to deploy app');
      const data = await res.json();
      
      // Navigate to Workspace to monitor new session
      navigate(`/workspace?session_id=${data.session_id}`);
    } catch (err) {
      console.error('Deploy error', err);
      const event = new CustomEvent('notify', { 
        detail: { type: 'error', message: 'Failed to run app' } 
      });
      window.dispatchEvent(event);
    }
  };

  const handleDelete = async (appId) => {
    if (!window.confirm("Are you sure you want to delete this app?")) return;
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`http://localhost:8000/apps/${appId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!res.ok) throw new Error('Failed to delete app');
      await fetchApps();
      const event = new CustomEvent('notify', { 
        detail: { type: 'success', message: 'App deleted successfully' } 
      });
      window.dispatchEvent(event);
    } catch (err) {
      console.error(err);
      const event = new CustomEvent('notify', { 
        detail: { type: 'error', message: 'Failed to delete app' } 
      });
      window.dispatchEvent(event);
    }
  };

  return (
    <div className="min-h-screen pb-20 max-w-7xl mx-auto pt-6 px-4">
      <div className="flex flex-col mb-8 gap-4">
        <h1 className="text-3xl sm:text-4xl font-bold text-white flex items-center gap-3">
          <Box className="w-8 h-8 text-white/70" />
          My Apps
        </h1>
        <p className="text-text-secondary text-base">
          Saved workflows ready to be deployed instantly without recompilation.
        </p>
      </div>

      <div className="glass-panel p-6 rounded-2xl min-h-[50vh]">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold flex items-center gap-2 text-white">
            <HardDrive size={18} />
            Library
          </h2>
          <button onClick={fetchApps} className="text-text-secondary hover:text-white transition-colors" disabled={loading}>
            <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm mb-6">
            Error loading apps: {error}
          </div>
        )}

        {loading ? (
          <div className="flex justify-center items-center py-20 text-white/50">
            <RefreshCw className="animate-spin mr-3" size={24} /> Loading apps...
          </div>
        ) : apps.length === 0 ? (
          <div className="text-center py-16">
            <Box className="mx-auto w-12 h-12 text-white/20 mb-4" />
            <h3 className="text-lg font-medium text-white mb-2">No apps found</h3>
            <p className="text-text-secondary">
              Save workflows from the workspace to use them as reusable apps.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {apps.map((app) => (
              <motion.div
                key={app.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="group relative flex flex-col justify-between p-5 rounded-xl border border-white/10 bg-black/40 hover:bg-white/5 hover:border-white/20 transition-all shadow-lg"
              >
                <div className="mb-4">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="text-lg font-bold text-white truncate pr-4">{app.name}</h3>
                    <button
                      onClick={() => handleDelete(app.id)}
                      className="p-1.5 text-text-tertiary hover:text-red-400 hover:bg-red-400/10 rounded-md transition-colors opacity-0 group-hover:opacity-100 absolute top-4 right-4"
                      title="Delete App"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                  <div className="text-xs font-mono text-text-tertiary truncate">
                    ID: {app.id.substring(0, 8)}...
                  </div>
                </div>

                <div className="flex justify-between items-center mt-auto pt-4 border-t border-white/5">
                  <span className="text-xs text-text-secondary flex items-center gap-1.5">
                    <Calendar size={12} />
                    {new Date(app.updated_at || app.created_at).toLocaleDateString()}
                  </span>
                  
                  <button
                    onClick={() => handleDeploy(app.id)}
                    className="flex items-center gap-2 px-3 py-1.5 bg-white text-black hover:bg-gray-200 rounded-md text-xs font-bold transition-all transform hover:scale-105 active:scale-95 shadow-lg"
                  >
                    <Play size={12} fill="currentColor" />
                    Deploy
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Apps;
