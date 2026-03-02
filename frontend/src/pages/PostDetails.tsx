import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { getPost, updatePost } from '../services/api';

export default function PostDetails() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();

    const [post, setPost] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [isEditing, setIsEditing] = useState(false);
    const [editForm, setEditForm] = useState<any>(null);
    const [selectedIndexes, setSelectedIndexes] = useState<number[]>([]);

    useEffect(() => {
        const fetchPost = async () => {
            if (!id) return;
            try {
                const { data } = await getPost(id);
                setPost(data);
                setEditForm(JSON.parse(JSON.stringify(data)));
            } catch (error) {
                toast.error('Post not found');
                navigate('/dashboard');
            } finally {
                setLoading(false);
            }
        };
        fetchPost();
    }, [id, navigate]);

    // --- BULK SELECTION LOGIC ---
    const toggleSelect = (index: number) => {
        setSelectedIndexes(prev => 
            prev.includes(index) ? prev.filter(i => i !== index) : [...prev, index]
        );
    };

    const handleSelectAll = () => {
        if (selectedIndexes.length === editForm.comments.length) {
            setSelectedIndexes([]);
        } else {
            setSelectedIndexes(editForm.comments.map((_: any, i: number) => i));
        }
    };

    const handleBulkDelete = () => {
        if (!window.confirm(`Delete ${selectedIndexes.length} selected comments?`)) return;
        const newComments = editForm.comments.filter((_: any, i: number) => !selectedIndexes.includes(i));
        setEditForm({ ...editForm, comments: newComments });
        setSelectedIndexes([]);
        toast.success('Comments removed from local view');
    };

    const handleSave = async () => {
        try {
            await updatePost(id!, editForm);
            setPost(editForm);
            setIsEditing(false);
            setSelectedIndexes([]);
            toast.success('Changes saved to database');
        } catch (error) {
            toast.error('Update failed');
        }
    };

    const handleCancel = () => {
        setEditForm(JSON.parse(JSON.stringify(post)));
        setIsEditing(false);
        setSelectedIndexes([]);
    };

    const removeComment = (index: number) => {
        const newComments = editForm.comments.filter((_: any, i: number) => i !== index);
        setEditForm({ ...editForm, comments: newComments });
    };

    const handleCommentChange = (index: number, val: string) => {
        const newComments = [...editForm.comments];
        newComments[index].text = val;
        setEditForm({ ...editForm, comments: newComments });
    };

    if (loading) return <div className="py-20 text-center">Loading details...</div>;
    if (!post) return <div className="py-20 text-center text-red-500">Post not found.</div>;

    return (
        <div className="max-w-4xl mx-auto space-y-6 animate-fade-in pb-12 px-4">
            
            {/* STICKY ACTION BAR */}
            <div className="sticky top-4 z-50 flex justify-between items-center bg-white/90 backdrop-blur border border-gray-200 p-4 rounded-2xl shadow-lg">
                <button onClick={() => navigate('/dashboard')} className="text-gray-500 hover:text-gray-800 text-sm font-medium">
                    ← Back
                </button>
                
                <div className="flex gap-2">
                    {isEditing ? (
                        <>
                            {selectedIndexes.length > 0 && (
                                <button onClick={handleBulkDelete} className="px-4 py-2 text-sm font-bold text-white bg-red-500 hover:bg-red-600 rounded-lg shadow-sm">
                                    Delete Selected ({selectedIndexes.length})
                                </button>
                            )}
                            <button onClick={handleCancel} className="px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 rounded-lg">
                                Cancel
                            </button>
                            <button onClick={handleSave} className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg shadow-md hover:bg-blue-700">
                                Save changes
                            </button>
                        </>
                    ) : (
                        <button onClick={() => setIsEditing(true)} className="px-6 py-2 text-sm font-bold text-white bg-blue-600 rounded-lg shadow-md hover:bg-blue-700">
                            Edit & Clean Data
                        </button>
                    )}
                </div>
            </div>

            {/* MAIN POST */}
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">Original Post</h3>
                {isEditing ? (
                    <textarea
                        value={editForm.post_text}
                        onChange={(e) => setEditForm({ ...editForm, post_text: e.target.value })}
                        rows={4}
                        className="w-full p-4 border border-blue-100 bg-blue-50/30 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                    />
                ) : (
                    <p className="text-gray-800 leading-relaxed font-medium">{post.post_text}</p>
                )}
            </div>

            {/* COMMENTS SECTION */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
                    <h2 className="font-bold text-gray-900">
                        Comments ({isEditing ? editForm.comments.length : post.comments.length})
                    </h2>
                    {isEditing && (
                        <button onClick={handleSelectAll} className="text-sm font-semibold text-blue-600 hover:underline">
                            {selectedIndexes.length === editForm.comments.length ? 'Deselect All' : 'Select All'}
                        </button>
                    )}
                </div>

                <div className="divide-y divide-gray-100">
                    {(isEditing ? editForm.comments : post.comments).map((comment: any, idx: number) => (
                        <div key={idx} className={`p-4 flex gap-4 transition-colors ${selectedIndexes.includes(idx) ? 'bg-red-50' : 'hover:bg-gray-50/50'}`}>
                            {isEditing && (
                                <input 
                                    type="checkbox"
                                    checked={selectedIndexes.includes(idx)}
                                    onChange={() => toggleSelect(idx)}
                                    className="mt-1 h-5 w-5 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                                />
                            )}
                            
                            <div className="flex-1">
                                {isEditing ? (
                                    <div className="relative group">
                                        <textarea
                                            value={comment.text}
                                            onChange={(e) => handleCommentChange(idx, e.target.value)}
                                            rows={2}
                                            className="w-full p-3 text-sm border border-gray-200 rounded-xl focus:bg-white bg-gray-50/50 outline-none"
                                        />
                                        <button 
                                            onClick={() => removeComment(idx)}
                                            className="absolute -top-2 -right-2 bg-white text-gray-400 hover:text-red-500 rounded-full shadow-sm border border-gray-100 p-1"
                                        >
                                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"/></svg>
                                        </button>
                                    </div>
                                ) : (
                                    <p className="text-gray-700 text-sm leading-relaxed">{comment.text}</p>
                                )}
                                <p className="text-[10px] text-gray-400 mt-2 font-mono uppercase">{comment.date || 'No Date'}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}