import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Home from './pages/Home';
import Dashboard from './pages/Dashboard';
import PostDetails from './pages/PostDetails';

function Navbar() {
    return (
        <nav className="bg-white shadow">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between h-16">
                    <div className="flex space-x-8">
                        <Link to="/" className="flex items-center text-xl font-bold text-gray-900 hover:text-blue-600 transition-colors">
                            <span className="text-blue-600 mr-2">Oromoo</span> Scraper
                        </Link>
                        <div className="hidden sm:flex sm:space-x-8 items-center">
                            <Link to="/dashboard" className="text-gray-500 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium transition-colors">
                                Dashboard
                            </Link>
                        </div>
                    </div>
                </div>
            </div>
        </nav>
    );
}

function App() {
    return (
        <BrowserRouter>
            <div className="min-h-screen flex flex-col">
                <Navbar />
                <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <Routes>
                        <Route path="/" element={<Home />} />
                        <Route path="/dashboard" element={<Dashboard />} />
                        <Route path="/posts/:id" element={<PostDetails />} />
                    </Routes>
                </main>
            </div>
            <Toaster position="bottom-right" />
        </BrowserRouter>
    );
}

export default App;
