import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { verifyPassword } from '../services/api';

export default function Login() {
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            const response = await verifyPassword(password);
            localStorage.setItem('admin_token', response.token);
            toast.success('Login successful!');
            navigate('/dashboard'); // Or back to wherever they were trying to go
        } catch (error) {
            toast.error('Invalid password');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex items-center justify-center h-full pt-20">
            <div className="w-full max-w-md bg-white rounded-2xl p-8 shadow-sm border border-gray-100">
                <div className="text-center mb-8">
                    <h2 className="text-2xl font-bold text-gray-900">Admin Access</h2>
                    <p className="text-gray-500 mt-2">Enter the admin password to view and manage data.</p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Enter password"
                            className="w-full border-gray-200 rounded-lg p-3 text-sm focus:ring-emerald-500 focus:border-emerald-500 border"
                            required
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-emerald-600 text-white rounded-lg py-3 text-sm font-medium hover:bg-emerald-700 transition-colors disabled:opacity-50"
                    >
                        {loading ? 'Verifying...' : 'Login'}
                    </button>
                </form>
            </div>
        </div>
    );
}
