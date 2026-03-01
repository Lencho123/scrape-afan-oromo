import { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { getStats, getPosts, deletePost, downloadExport } from '../services/api';

export default function Dashboard() {
    const [stats, setStats] = useState({ total_posts: 0, total_comments: 0, total_tokens: 0 });
    const [posts, setPosts] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    // Filters
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');

    // Wrapped in useCallback so it can be called safely from useEffect and handlers
    const fetchData = useCallback(async (start?: string, end?: string) => {
        setLoading(true);
        try {
            // Use passed parameters or fallback to state
            const s = start !== undefined ? start : startDate;
            const e = end !== undefined ? end : endDate;

            const [{ data: statsData }, { data: postsData }] = await Promise.all([
                getStats(),
                getPosts(s, e)
            ]);
            setStats(statsData);
            setPosts(postsData);
        } catch (error) {
            toast.error('Failed to load dashboard data');
        } finally {
            setLoading(false);
        }
    }, [startDate, endDate]);

    useEffect(() => {
        fetchData();
    }, []); // Runs once on mount

    const handleFilter = (e: React.FormEvent) => {
        e.preventDefault();
        fetchData();
    };

    const handleClearFilters = () => {
        setStartDate('');
        setEndDate('');
        // Immediately fetch with empty strings to bypass state delay
        fetchData('', '');
    };

    const handleExport = async (format: string) => {
        try {
            toast.success(`Exporting ${format.toUpperCase()}...`);
            await downloadExport(format, startDate, endDate);
        } catch (error) {
            toast.error('Failed to export data');
        }
    };

    const handleDelete = async (postId: string) => {
        if (!window.confirm('Are you sure you want to delete this post?')) return;
        try {
            await deletePost(postId);
            toast.success('Post deleted');
            fetchData(); 
        } catch (error) {
            toast.error('Failed to delete post');
        }
    };

    return (
        <div className="space-y-8 animate-fade-in">
            <div className="flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
                    <p className="text-gray-500 mt-1">Overview of your scraped facebook data</p>
                </div>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {[
                    { label: 'Total Posts', value: stats.total_posts, color: 'text-blue-700', bg: 'bg-blue-50' },
                    { label: 'Total Comments', value: stats.total_comments, color: 'text-green-700', bg: 'bg-green-50' },
                    { label: 'Total Tokens', value: stats.total_tokens, color: 'text-purple-700', bg: 'bg-purple-50' }
                ].map((stat, i) => (
                    <div key={i} className={`bg-white rounded-2xl p-6 shadow-sm border border-gray-100 flex flex-col`}>
                        <span className="text-gray-500 font-medium text-sm">{stat.label}</span>
                        <span className={`text-3xl font-bold mt-2 ${stat.color}`}>
                            {stat.value.toLocaleString()}
                        </span>
                    </div>
                ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
                {/* Sidebar */}
                <div className="lg:col-span-1 space-y-6">
                    <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                        <h3 className="font-semibold text-gray-900 mb-4">Filter by Date</h3>
                        <form onSubmit={handleFilter} className="space-y-4">
                            <div>
                                <label className="block text-sm text-gray-600 mb-1">Start Date</label>
                                <input
                                    type="date"
                                    value={startDate}
                                    onChange={e => setStartDate(e.target.value)}
                                    className="w-full border-gray-200 rounded-lg p-2.5 text-sm focus:ring-blue-500 focus:border-blue-500"
                                />
                            </div>
                            <div>
                                <label className="block text-sm text-gray-600 mb-1">End Date</label>
                                <input
                                    type="date"
                                    value={endDate}
                                    onChange={e => setEndDate(e.target.value)}
                                    className="w-full border-gray-200 rounded-lg p-2.5 text-sm focus:ring-blue-500 focus:border-blue-500"
                                />
                            </div>
                            <button
                                type="submit"
                                className="w-full bg-gray-900 text-white rounded-lg py-2.5 text-sm font-medium hover:bg-gray-800 transition-colors"
                            >
                                Apply Filters
                            </button>
                            {(startDate || endDate) && (
                                <button
                                    type="button"
                                    onClick={handleClearFilters}
                                    className="w-full text-gray-600 rounded-lg py-2.5 text-sm font-medium hover:bg-gray-100 transition-colors"
                                >
                                    Clear Filters
                                </button>
                            )}
                        </form>
                    </div>

                    <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                        <h3 className="font-semibold text-gray-900 mb-4">Export Data</h3>
                        <div className="space-y-3">
                            <button onClick={() => handleExport('csv')} className="w-full flex justify-between items-center px-4 py-2 bg-blue-50 text-blue-700 hover:bg-blue-100 rounded-lg font-medium text-sm transition-colors">
                                Export to CSV <span>↓</span>
                            </button>
                            <button onClick={() => handleExport('json')} className="w-full flex justify-between items-center px-4 py-2 bg-green-50 text-green-700 hover:bg-green-100 rounded-lg font-medium text-sm transition-colors">
                                Export to JSON <span>↓</span>
                            </button>
                            <button onClick={() => handleExport('jsonl')} className="w-full flex justify-between items-center px-4 py-2 bg-purple-50 text-purple-700 hover:bg-purple-100 rounded-lg font-medium text-sm transition-colors">
                                Export to JSONL <span>↓</span>
                            </button>
                        </div>
                    </div>
                </div>

                {/* Table */}
                <div className="lg:col-span-3 bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                    <div className="px-6 py-5 border-b border-gray-100 flex justify-between items-center">
                        <h3 className="font-semibold text-gray-900">Scraped Posts</h3>
                        <button onClick={() => fetchData()} className="text-sm text-blue-600 hover:text-blue-800 font-medium">
                            Refresh
                        </button>
                    </div>

                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Preview</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Comments</th>
                                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-100">
                                {loading ? (
                                    <tr>
                                        <td colSpan={4} className="px-6 py-12 text-center text-gray-500">Loading posts...</td>
                                    </tr>
                                ) : posts.length === 0 ? (
                                    <tr>
                                        <td colSpan={4} className="px-6 py-12 text-center text-gray-500">No data found.</td>
                                    </tr>
                                ) : (
                                    posts.map((post) => (
                                        <tr key={post.post_id || post._id} className="hover:bg-gray-50 transition-colors">
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                                                {post.post_date || 'N/A'}
                                            </td>
                                            <td className="px-6 py-4 text-sm text-gray-900 truncate max-w-xs">
                                                {post.post_text}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 font-medium">
                                                {post.comments?.length || 0}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-3">
                                                <Link to={`/posts/${post.post_id}`} className="text-blue-600 hover:text-blue-900">View/Edit</Link>
                                                <button onClick={() => handleDelete(post.post_id)} className="text-red-500 hover:text-red-700">Delete</button>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
}