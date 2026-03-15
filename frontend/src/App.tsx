import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Home from './pages/Home';
import Dashboard from './pages/Dashboard';
import PostDetails from './pages/PostDetails';
import CleanData from './pages/CleanData';
import Login from './pages/Login';
import ProtectedRoute from './components/ProtectedRoute';

function Navbar() {
    const location = useLocation();

    // Do not show navbar on login page
    if (location.pathname === '/login') return null;

    // Helper to determine active link
    const isActive = (path: string) => location.pathname === path;

    const handleLogout = () => {
        localStorage.removeItem('admin_token');
        window.location.href = '/login';
    };

    return (
        <nav className="bg-white shadow">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between h-16">
                    <div className="flex space-x-8 items-center">
                        <Link to="/" className="flex items-center text-xl font-bold text-gray-900 hover:text-emerald-600 transition-colors">
                            <span className="text-emerald-600 mr-2">Oromoo</span> Scraper
                        </Link>
                        <div className="hidden sm:flex sm:space-x-8 items-center h-full">
                            <Link
                                to="/"
                                className={`h-full inline-flex items-center px-3 border-b-2 text-sm font-medium transition-colors ${isActive('/') ? 'border-emerald-500 text-gray-900' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}
                            >
                                Scrape
                            </Link>
                            <Link
                                to="/dashboard"
                                className={`h-full inline-flex items-center px-3 border-b-2 text-sm font-medium transition-colors ${isActive('/dashboard') ? 'border-emerald-500 text-gray-900' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}
                            >
                                Dashboard
                            </Link>
                            <Link
                                to="/clean-data"
                                className={`h-full inline-flex items-center px-3 border-b-2 text-sm font-medium transition-colors ${isActive('/clean-data') ? 'border-emerald-500 text-emerald-700 font-semibold' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}
                            >
                                Clean Data ✨
                            </Link>
                        </div>
                    </div>
                    <div className="flex items-center">
                        <button onClick={handleLogout} className="text-sm font-medium text-gray-500 hover:text-gray-700 transition-colors">
                            Logout
                        </button>
                    </div>
                </div>
            </div>
        </nav>
    );
}

function App() {
    return (
        <BrowserRouter>
            <div className="min-h-screen flex flex-col bg-gray-50/50">
                <Navbar />
                <main className="flex-1 w-full max-w-7xl mx-auto sm:px-6 lg:px-8 py-8 h-full">
                    <Routes>
                        <Route path="/login" element={<Login />} />
                        <Route element={<ProtectedRoute />}>
                            <Route path="/" element={<Home />} />
                            <Route path="/dashboard" element={<Dashboard />} />
                            <Route path="/clean-data" element={<CleanData />} />
                            <Route path="/posts/:id" element={<PostDetails />} />
                        </Route>
                    </Routes>
                </main>
            </div>
            <Toaster position="top-center" toastOptions={{ duration: 4000 }} />
        </BrowserRouter>
    );
}

export default App;
