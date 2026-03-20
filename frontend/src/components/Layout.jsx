import Navbar from './Navbar';
import Sidebar from './Sidebar';
import Footer from './Footer';

const Layout = ({ children }) => {
  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden bg-background font-sans text-text-primary selection:bg-white selection:text-black">
      {/* Background Elements */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden -z-10 mesh-bg opacity-40"></div>
      
      <Navbar />
      <Sidebar />
      <main className="flex-grow pt-24 sm:pt-28 md:pt-32 px-4 sm:px-6 pb-24 md:pb-0 md:pl-[120px] md:peer-hover:pl-[296px] transition-all duration-500 ease-[cubic-bezier(0.23,1,0.32,1)]">
        {children}
      </main>
      <Footer />
    </div>
  );
};

export default Layout;
