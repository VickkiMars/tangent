import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate, useLocation } from 'react-router-dom';
import { Mail, Lock, User, ArrowRight, Loader2, KeyRound, Sparkles, Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { authLogin, authSignup } from '../api';
import { notify } from '../components/Notification';

const Auth = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { login } = useAuth();

  const [isLogin, setIsLogin] = useState(location.pathname === '/login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  useEffect(() => {
    setIsLogin(location.pathname === '/login');
  }, [location.pathname]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const data = isLogin
        ? await authLogin(email, password)
        : await authSignup(email, password, firstName, lastName);
      await login(data.access_token);
      navigate('/chat');
    } catch (err) {
      notify(err.message || 'Connection failed. Please check your network.', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-3rem)] sm:min-h-[calc(100vh-3.5rem)] md:min-h-[calc(100vh-4rem)] flex items-center justify-center p-4 relative overflow-hidden bg-[#050505]">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,_rgba(255,255,255,0.03)_0%,_transparent_50%)]" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/5 rounded-full blur-[120px] opacity-20" />

      <motion.div
        initial={{ opacity: 0, scale: 0.98, y: 8 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
        className="w-full max-w-[360px] z-10"
      >
        <div className="relative group">
          <div className="absolute -inset-[1px] bg-gradient-to-b from-white/10 to-transparent rounded-3xl opacity-20 group-hover:opacity-30 transition-opacity" />

          <div className="relative bg-[#0A0A0A]/80 backdrop-blur-[32px] px-6 py-7 rounded-3xl border border-white/[0.06] shadow-[0_24px_80px_rgba(0,0,0,0.8)]">

            {/* Header */}
            <div className="text-center mb-5">
              <motion.div
                className="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-white/[0.03] border border-white/[0.06] mb-3"
                whileHover={{ scale: 1.05 }}
              >
                {isLogin ? <KeyRound className="text-white w-5 h-5" /> : <Sparkles className="text-white w-5 h-5" />}
              </motion.div>
              <h1 className="text-2xl font-semibold text-white tracking-tight mb-1">
                {isLogin ? 'Welcome back' : 'Get started'}
              </h1>
              <p className="text-text-secondary text-xs font-medium">
                {isLogin ? 'Access your intelligent workspace' : 'Begin your journey with Tangent'}
              </p>
            </div>

            {/* Tab Switcher */}
            <div className="flex p-1 bg-white/[0.03] rounded-2xl border border-white/[0.06] mb-5 relative">
              <motion.div
                className="absolute inset-y-1 left-1 w-[calc(50%-4px)] bg-white shadow-xl rounded-xl"
                animate={{ x: isLogin ? 0 : '100%' }}
                transition={{ type: "spring", stiffness: 300, damping: 30 }}
              />
              <button
                onClick={() => navigate('/login')}
                className={`flex-1 py-2 text-xs font-bold relative z-10 transition-colors duration-300 ${isLogin ? 'text-black' : 'text-text-tertiary hover:text-white'}`}
              >
                Login
              </button>
              <button
                onClick={() => navigate('/signup')}
                className={`flex-1 py-2 text-xs font-bold relative z-10 transition-colors duration-300 ${!isLogin ? 'text-black' : 'text-text-tertiary hover:text-white'}`}
              >
                Sign Up
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-3">
              <AnimatePresence mode="wait">
                {!isLogin && (
                  <motion.div
                    key="name-fields"
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="overflow-hidden"
                  >
                    <div className="flex gap-2">
                      <div className="relative group/field flex-1">
                        <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-tertiary group-focus-within/field:text-primary transition-colors" />
                        <input
                          type="text"
                          value={firstName}
                          onChange={(e) => setFirstName(e.target.value)}
                          placeholder="First name"
                          className="w-full bg-white/[0.02] border border-white/[0.08] rounded-xl py-2.5 pl-10 pr-3 text-sm text-white placeholder:text-text-tertiary focus:outline-none focus:ring-1 focus:ring-primary/40 focus:border-primary/40 focus:bg-white/[0.04] transition-all"
                          required={!isLogin}
                        />
                      </div>
                      <div className="relative group/field flex-1">
                        <input
                          type="text"
                          value={lastName}
                          onChange={(e) => setLastName(e.target.value)}
                          placeholder="Last name"
                          className="w-full bg-white/[0.02] border border-white/[0.08] rounded-xl py-2.5 pl-3 pr-3 text-sm text-white placeholder:text-text-tertiary focus:outline-none focus:ring-1 focus:ring-primary/40 focus:border-primary/40 focus:bg-white/[0.04] transition-all"
                          required={!isLogin}
                        />
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              <div className="relative group/field">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-tertiary group-focus-within/field:text-primary transition-colors" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Email"
                  className="w-full bg-white/[0.02] border border-white/[0.08] rounded-xl py-2.5 pl-10 pr-3 text-sm text-white placeholder:text-text-tertiary focus:outline-none focus:ring-1 focus:ring-primary/40 focus:border-primary/40 focus:bg-white/[0.04] transition-all"
                  required
                />
              </div>

              <div className="relative group/field">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-tertiary group-focus-within/field:text-primary transition-colors" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Password"
                  className="w-full bg-white/[0.02] border border-white/[0.08] rounded-xl py-2.5 pl-10 pr-10 text-sm text-white placeholder:text-text-tertiary focus:outline-none focus:ring-1 focus:ring-primary/40 focus:border-primary/40 focus:bg-white/[0.04] transition-all"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(v => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary hover:text-white transition-colors"
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                </button>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full relative group/btn h-10 rounded-xl bg-white text-black text-sm font-bold overflow-hidden transition-all active:scale-[0.98] disabled:opacity-50"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-transparent opacity-0 group-hover/btn:opacity-100 transition-opacity" />
                <span className="relative z-10 flex items-center justify-center gap-2">
                  {loading ? (
                    <Loader2 className="animate-spin w-4 h-4" />
                  ) : (
                    <>
                      {isLogin ? 'Sign In' : 'Create Account'}
                      <ArrowRight className="w-3.5 h-3.5 group-hover/btn:translate-x-0.5 transition-transform" />
                    </>
                  )}
                </span>
              </button>
            </form>

            <p className="mt-4 text-center text-[10px] text-text-tertiary leading-relaxed">
              By continuing you agree to our{' '}
              <span className="text-white/60 cursor-pointer hover:text-white transition-colors">Terms</span>
              {' '}&{' '}
              <span className="text-white/60 cursor-pointer hover:text-white transition-colors">Privacy Policy</span>
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default Auth;
