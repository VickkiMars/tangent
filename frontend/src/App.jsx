import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Landing from './pages/Landing';
import Workspace from './pages/Workspace';
import TaskView from './pages/TaskView';
import History from './pages/History';
import Pricing from './pages/Pricing';
import Features from './pages/Features';
import Docs from './pages/Docs';
import Chat from './pages/Chat';
import Builder from './pages/Builder';
import Auth from './pages/Auth';
import Notification from './components/Notification';
import { AuthProvider } from './context/AuthContext';
import './App.css';

function App() {
  return (
    <Router>
      <AuthProvider>
        <Layout>
          <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/workspace" element={<Workspace />} />
          <Route path="/builder" element={<Builder />} />
          <Route path="/tasks" element={<TaskView />} />
          <Route path="/history" element={<History />} />
          <Route path="/pricing" element={<Pricing />} />
          <Route path="/docs" element={<Docs />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/login" element={<Auth />} />
          <Route path="/signup" element={<Auth />} />
        </Routes>
        <Notification />
      </Layout>
      </AuthProvider>
    </Router>
  );
}

export default App;
