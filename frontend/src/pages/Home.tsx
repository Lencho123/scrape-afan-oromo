import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { triggerScrape } from '../services/api';

export default function Home() {
    const [url, setUrl] = useState('');
    const [isScraping, setIsScraping] = useState(false);
    const navigate = useNavigate();

    const handleScrape = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanUrl = url.trim();

    if (!cleanUrl.includes('facebook.com')) {
        toast.error('Enter a valid Facebook URL');
        return;
    }

    setIsScraping(true);
    try {
        // Passing the URL inside the expected object structure
        await triggerScrape(cleanUrl); 
        toast.success('Scraping session queued!');
        navigate('/dashboard');
    } catch (error: any) {
        toast.error('Error: ' + error.response?.data?.detail || 'Server unreachable');
    } finally {
        setIsScraping(false);
    }
};

    return (
        <div className="flex items-center justify-center min-h-[80vh]">
            <div className="w-full max-w-2xl bg-white shadow-xl rounded-2xl p-8 sm:p-12 text-center border border-gray-100">
                <h1 className="text-3xl sm:text-4xl font-extrabold text-gray-900 tracking-tight mb-4">
                    Facebook Afaan Oromoo Scraper
                </h1>
                <p className="text-gray-500 mb-8 max-w-lg mx-auto">
                    Easily extract, store, and manage Afaan Oromoo text data from Facebook posts and comments.
                </p>

                <form onSubmit={handleScrape} className="w-full relative group">
                    <input
                        type="url"
                        name="url"
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        required
                        className="w-full text-base sm:text-lg px-6 py-4 bg-gray-50 border border-gray-200 rounded-xl focus:ring-4 focus:ring-blue-50 focus:border-blue-500 outline-none transition-all duration-200"
                        placeholder="Paste Facebook Post URL here..."
                    />
                    <button
                        type="submit"
                        disabled={isScraping}
                        className={`mt-6 w-full sm:w-auto px-10 py-4 font-semibold text-white rounded-xl shadow-md transition-all duration-200 text-lg
              ${isScraping ? 'bg-blue-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 hover:shadow-lg active:scale-95'}`}
                    >
                        {isScraping ? (
                            <span className="flex items-center justify-center">
                                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                Scraping Post...
                            </span>
                        ) : (
                            'Scrape Post'
                        )}
                    </button>
                </form>
            </div>
        </div>
    );
}
