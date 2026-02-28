import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { getPost, updatePost, deletePost } from '../services/api';

export default function PostDetails() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();

    const [post, setPost] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [isEditing, setIsEditing] = useState(false);
    const [editForm, setEditForm] = useState<any>(null);

    useEffect(() => {
        const fetchPost = async () => {
            try {
                const { data } = await getPost(id!);
                setPost(data);
                setEditForm(JSON.parse(JSON.stringify(data))); // deep copy
            } catch (error) {
                toast.error('Failed to load post details');
                navigate('/dashboard');
            } finally {
                setLoading(false);
            }
        };
        fetchPost();
    }, [id, navigate]);

    const handleSave = async () => {
        try {
            await updatePost(id!, editForm);
            setPost(editForm);
            setIsEditing(false);
            toast.success('Post updated safely');
        } catch (error) {
            toast.error('Failed to update post');
        }
    };

    const handleDelete = async () => {
        if (!window.confirm('Permanent delete. Are you sure?')) return;
        try {
            await deletePost(id!);
            toast.success('Post deleted');
            navigate('/dashboard');
        } catch (error) {
            toast.error('Failed to delete post');
        }
    };

    const handleCommentChange = (index: number, val: string) => {
        const newComments = [...editForm.comments];
        newComments[index].text = val;
        setEditForm({ ...editForm, comments: newComments });
    };

    if (loading) return <div className="py-20 text-center">Loading details...</div>;
    if (!post) return <div className="py-20 text-center text-red-500">Post not found.</div>;

    return (
        <div className="max-w-4xl mx-auto space-y-8 animate-fade-in pb-12">
            {/* Header Actions */}
            <div className="flex justify-between items-center bg-white p-4 rounded-xl shadow-sm border border-gray-100">
                <button onClick={() => navigate('/dashboard')} className="text-gray-500 hover:text-gray-900 font-medium text-sm flex items-center">
                    ← Back
                </button>
                <div className="space-x-3">
                    {isEditing ? (
                        <div className="flex space-x-2">
                            <button onClick={() => setIsEditing(false)} className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg">Cancel</button>
                            <button onClick={handleSave} className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg">Save Changes</button>
                        </div>
                    ) : (
                        <div className="flex space-x-2">
                            <button onClick={() => setIsEditing(true)} className="px-4 py-2 text-sm font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-lg">Edit Mode</button>
                            <button onClick={handleDelete} className="px-4 py-2 text-sm font-medium text-red-700 bg-red-50 hover:bg-red-100 rounded-lg">Delete</button>
                        </div>
                    )}
                </div>
            </div>

            {/* Main Post Section */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <div className="flex justify-between mb-4">
                    <h2 className="text-lg font-semibold text-gray-900">Main Post Content</h2>
                    <span className="text-sm text-gray-500 px-3 py-1 bg-gray-100 rounded-full">{post.post_date}</span>
                </div>

                {isEditing ? (
                    <textarea
                        value={editForm.post_text}
                        onChange={(e) => setEditForm({ ...editForm, post_text: e.target.value })}
                        rows={5}
                        className="w-full p-4 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none resize-y"
                    />
                ) : (
                    <p className="whitespace-pre-wrap text-gray-700 leading-relaxed font-medium bg-gray-50 p-6 rounded-xl border border-gray-100">
                        {post.post_text}
                    </p>
                )}
            </div>

            {/* Comments Section */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h2 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
                    Comments
                    <span className="ml-3 bg-blue-100 text-blue-800 text-xs py-1 px-2.5 rounded-full">{post.comments.length}</span>
                </h2>

                <div className="space-y-4">
                    {post.comments.length === 0 ? (
                        <p className="text-center text-gray-500 py-6 bg-gray-50 rounded-lg">No comments extracted for this post.</p>
                    ) : (
                        (isEditing ? editForm.comments : post.comments).map((comment: any, idx: number) => (
                            <div key={idx} className="flex flex-col sm:flex-row gap-4 p-4 border border-gray-100 rounded-xl hover:bg-gray-50 transition-colors">
                                <div className="sm:w-32 flex-shrink-0">
                                    <span className="text-xs font-medium text-gray-500">{comment.date || 'Unknown date'}</span>
                                </div>
                                <div className="flex-1">
                                    {isEditing ? (
                                        <textarea
                                            value={comment.text}
                                            onChange={(e) => handleCommentChange(idx, e.target.value)}
                                            rows={2}
                                            className="w-full p-2.5 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                                        />
                                    ) : (
                                        <p className="text-gray-700 text-sm">{comment.text}</p>
                                    )}
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
}
