import { useState, useEffect } from 'react';
import {
  Settings,
  User,
  MessageSquare,
  Zap,
  Code,
  FileText,
  ChevronRight,
  Menu,
  X,
  PlusCircle,
  WandSparkles
} from 'lucide-react';
import UserProfile from '@/features/dashboard/components/UserProfile';
import { useNavigate } from 'react-router-dom';

// Mock data for previous projects
const mockProjects = [
  { id: 1, name: 'E-commerce Cart Page', date: '2 hours ago', icon: <Zap className="w-4 h-4 text-gray-400" /> },
  { id: 2, name: 'Client Onboarding Flow', date: 'Yesterday', icon: <Code className="w-4 h-4 text-gray-400" /> },
  { id: 3, name: 'SaaS Analytics Dashboard', date: '3 days ago', icon: <FileText className="w-4 h-4 text-gray-400" /> },
];


/**
 * Renders a card for a previous project.
 */
const ProjectCard = ({ project }) => (
  <div className="bg-gray-800/50 p-4 rounded-xl shadow-lg hover:shadow-xl transition-shadow duration-300 border border-gray-800 hover:border-gray-600 cursor-pointer flex flex-col justify-between h-full">
    <div className="flex items-center space-x-3 mb-4">
      <div className="p-2 bg-gray-800 rounded-full">{project.icon}</div>
      <h3 className="text-lg font-semibold text-gray-100 truncate">{project.name}</h3>
    </div>
    <div className="flex justify-between items-end">
      <p className="text-xs text-gray-400">Last accessed: {project.date}</p>
      {/* Changed accent color to gray-400/white on hover */}
      <ChevronRight className="w-4 h-4 text-gray-500 transition group-hover:text-white" />
    </div>
  </div>
);

/**
 * Simple Modal component for feedback.
 */
const FeedbackModal = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-70 p-4 cursor-pointer" onClick={onClose}>
      <div
        className="bg-gray-800/50 rounded-xl shadow-2xl w-full max-w-lg transform transition-all duration-300 scale-100 border border-gray-800 cursor-default"
        onClick={(e) => e.stopPropagation()} // Prevent closing when clicking inside
      >
        <div className="p-6">
          <h2 className="text-2xl font-bold text-white mb-4 flex items-center justify-between">
            Send Feedback
            <X className="w-6 h-6 text-gray-400 cursor-pointer hover:text-white transition" onClick={onClose} />
          </h2>
          <p className="text-gray-300 mb-4">Help us improve D-burst! What are your thoughts?</p>
          <textarea
            className="w-full h-32 p-3 border border-gray-700 rounded-lg focus:ring-blue-600 focus:border-blue-600 resize-none bg-gray-800 text-white placeholder-gray-500 transition duration-200"
            placeholder="I love the new Code Writer feature, but..."
          ></textarea>
          <div className="mt-4 flex justify-end">
            <button
              className="px-4 py-2 bg-blue-600 text-white font-medium rounded-lg shadow-md hover:bg-blue-700 transition duration-150 cursor-pointer"
              onClick={() => {
                // Placeholder for submission logic
                console.log('Feedback submitted');
                onClose();
              }}
            >
              Submit
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};


// --- Main App Component ---

const App = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const userName = 'Guest User'; // Should be replaced with actual user name from auth context

  // Basic menu items for the sidebar/dropdown
  const menuItems = [
    { name: 'Settings', icon: Settings, action: () => console.log('Go to settings'), className: 'hover:bg-gray-800' },
    { name: 'Give Feedback', icon: MessageSquare, action: () => setIsModalOpen(true), className: 'hover:bg-gray-800' },
    { name: 'Log Out', icon: User, action: () => console.log('Logging out...'), className: 'text-red-400 hover:bg-gray-800' },
  ];

  const navigate = useNavigate();

  // Close sidebar on screen size change
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 1024) {
        setIsSidebarOpen(false);
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);


  return (
    // Background color matching the login page
    <div className="min-h-screen bg-[#0A0A0A] font-sans">
      <FeedbackModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />

      {/* Mobile Sidebar/Menu Overlay */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black bg-opacity-70 lg:hidden"
          onClick={() => setIsSidebarOpen(false)}
        ></div>
      )}

      {/* Sidebar Content (Hidden on large screens, slides in on mobile) */}
      <div
        className={`fixed top-0 left-0 h-full w-64 bg-gray-900 shadow-2xl z-50 transform transition-transform duration-300 ease-in-out lg:hidden border-r border-gray-800 ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="p-6 flex flex-col space-y-4">
          <div className="flex justify-between items-center mb-4">
            {/* Header set to pure white */}
            <h2 className="text-xl font-bold text-white">D-burst Menu</h2>
            <X className="w-6 h-6 text-gray-400 cursor-pointer hover:text-white transition" onClick={() => setIsSidebarOpen(false)} />
          </div>

          <UserProfile userName={userName} onUserClick={() => console.log('View full profile')} />

          <hr className="border-gray-800" />

          {menuItems.map((item) => (
            <button
              key={item.name}
              onClick={() => {
                item.action();
                setIsSidebarOpen(false);
              }}
              className={`flex items-center space-x-3 p-3 text-gray-200 font-medium rounded-lg transition-colors duration-150 w-full text-left cursor-pointer ${item.className}`}
            >
              <item.icon className="w-5 h-5" />
              <span>{item.name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Main Layout Container */}
      <header className="bg-gray-900/20 shadow-lg sticky top-0 z-30 border-b border-gray-800 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex justify-between items-center h-16">
          <div className="flex items-center space-x-4">
            {/* Mobile Menu Button */}
            <button
              className="lg:hidden p-2 rounded-lg text-gray-300 hover:bg-gray-800 transition cursor-pointer"
              onClick={() => setIsSidebarOpen(true)}
            >
              <Menu className="w-6 h-6" />
            </button>

            {/* Logo/Project Title - Set to pure white */}
            <div className="text-2xl font-extrabold tracking-tight text-white">
              D-burst
            </div>
            <span className="hidden sm:block text-sm font-medium text-gray-500">AI Frontend Builder</span>
          </div>

          <div className="flex items-center space-x-2 md:space-x-4">
            {/* Desktop Navigation/Actions */}
            <button
              className="hidden lg:flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-200 rounded-lg hover:bg-gray-800 transition cursor-pointer"
              onClick={() => setIsModalOpen(true)}
            >
              <MessageSquare className="w-5 h-5 text-gray-400" />
              <span>Feedback</span>
            </button>

            <button
              className="hidden lg:flex p-2 text-gray-300 rounded-lg hover:bg-gray-800 transition cursor-pointer"
              onClick={() => console.log('Go to settings')}
            >
              <Settings className="w-6 h-6" />
            </button>

            <UserProfile userName={userName} onUserClick={() => console.log('View full profile')} />
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {/* New Project / Code Writer Section */}
        <div className="bg-gray-800/50 p-6 sm:p-8 rounded-2xl shadow-xl border border-gray-800 mb-10">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center">
            <div className="mb-4 sm:mb-0">
              <h1 className="text-3xl font-bold text-white flex items-center space-x-3">
                <span className="text-white">Start a New Project</span>
              </h1>
              <p className="mt-1 text-lg text-gray-400">Generate UI from a single text prompt.</p>
            </div>
            <button
              className="w-full sm:w-auto px-6 py-3 bg-gray-500/20 underline text-white font-semibold rounded-xl shadow-lg hover:bg-gray-500 transition transform hover:scale-[1.01] duration-200 flex items-center justify-center space-x-2 cursor-pointer"
              onClick={() => navigate('/dashboard/ui-generator')}
            >
              <WandSparkles className="w-5 h-5" />
              <span>Advanced Building</span>
            </button>
            <button
              className="w-full sm:w-auto px-6 py-3 bg-blue-600 text-white font-semibold rounded-xl shadow-lg hover:bg-blue-700 transition transform hover:scale-[1.01] duration-200 flex items-center justify-center space-x-2 cursor-pointer"
              onClick={() => console.log('Open New Project Modal/Page')}
            >
              <PlusCircle className="w-5 h-5" />
              <span>Submit</span>
            </button>
          </div>
          <div className="mt-6">
            <textarea
              className="w-full h-24 p-4 border-2 border-gray-700 rounded-xl focus:ring-blue-600 focus:border-blue-600 bg-gray-800 text-white placeholder-gray-500 resize-none transition duration-200"
              placeholder="e.g., 'A responsive, dark-mode pricing page with three tiers and a clean design using Tailwind CSS'"
            ></textarea>
          </div>
        </div>

        {/* Previous Projects Section */}
        <section className="mt-12">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-white">
              Recent Projects
            </h2>
            <button
              className="flex items-center text-gray-400 font-medium text-base hover:text-white transition cursor-pointer"
              onClick={() => console.log('Go to All Projects')}
            >
              View All Projects
              <ChevronRight className="w-4 h-4 ml-1" />
            </button>
          </div>

          {/* Project Grid - Shows max 3, automatically responsive */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {mockProjects.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}

            {/* "More" option card, visually distinct */}
            {/* <div
              className="border-2 border-dashed border-gray-700 p-4 rounded-xl flex items-center justify-center cursor-pointer hover:bg-gray-800 transition duration-150 h-full min-h-[120px]"
              onClick={() => console.log('Go to All Projects')}
            >
              <div className="text-center">
                <PlusCircle className="w-8 h-8 mx-auto text-gray-500 mb-2" />
                <p className="text-sm font-medium text-gray-400">More Projects</p>
              </div>
            </div> */}
          </div>
        </section>
      </main>
    </div>
  );
};

export default App;