import Navbar from './Navbar';
import Footer from './Footer';

const Layout = ({ children }) => {
  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden bg-background font-sans text-text-primary selection:bg-white selection:text-black">
      {/* Background Elements */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden -z-10 mesh-bg opacity-40"></div>
      <div className="fixed bottom-0 left-0 right-0 h-64 bg-gradient-to-t from-orange/10 via-white/5 to-transparent pointer-events-none -z-10"></div>
      
      <Navbar />
      <main className="flex-grow pt-32 px-6">
        {children}
      </main>
      <Footer />
    </div>
  );
};

export default Layout;
