import { useState } from 'react';
import { toast } from 'react-hot-toast';
import { uploadForCleaning } from '../services/api';
import Papa from 'papaparse';

export default function CleanData() {
    const [file, setFile] = useState<File | null>(null);
    const [isCleaning, setIsCleaning] = useState(false);
    const [stats, setStats] = useState<any>(null);
    const [cleanedData, setCleanedData] = useState<any[]>([]);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
            // Reset state on new file
            setStats(null);
            setCleanedData([]);
        }
    };

    const handleClean = async () => {
        if (!file) {
            toast.error("Please select a file first.");
            return;
        }

        setIsCleaning(true);
        try {
            const response = await uploadForCleaning(file);
            setStats(response.stats);
            setCleanedData(response.cleaned_data);
            toast.success("Data cleaned successfully!");
        } catch (error: any) {
            toast.error('Error cleaning data: ' + error.response?.data?.detail || 'Server unreachable');
        } finally {
            setIsCleaning(false);
        }
    };

    // --- In-Browser Export Utils for Cleaned Payload ---
    const handleExport = (format: 'json' | 'jsonl' | 'csv') => {
        if (!cleanedData || cleanedData.length === 0) {
            toast.error("No data to export.");
            return;
        }

        let content = '';
        let type = 'application/octet-stream';
        let fileExt = format;

        if (format === 'json') {
            content = JSON.stringify(cleanedData, null, 2);
            type = 'application/json';
        } else if (format === 'jsonl') {
            content = cleanedData.map(post => JSON.stringify(post)).join('\n');
            type = 'application/x-ndjson';
        } else if (format === 'csv') {
            // Flatten comments back into JSON string for CSV
            const csvData = cleanedData.map(post => ({
                ...post,
                comments: typeof post.comments !== 'string'
                    ? JSON.stringify(post.comments || [])
                    : post.comments
            }));

            // utf-8 BOM for excel
            content = "\ufeff" + Papa.unparse(csvData);
            type = 'text/csv;charset=utf-8';
        }

        const blob = new Blob([content], { type });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        const timestamp = new Date().toISOString().split('T')[0];
        link.setAttribute('download', `cleaned_data_${timestamp}.${fileExt}`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    };

    return (
        <div className="max-w-6xl mx-auto px-4 py-8">
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 sm:p-12 transition-all duration-300">
                <div className="mb-10 text-center">
                    <h1 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl mb-3 border-l-4 border-emerald-500 inline-block pl-4 text-left w-full max-w-2xl">
                        Clean Data
                    </h1>
                    <p className="max-w-2xl mx-auto text-lg text-gray-500 text-left">
                        Upload a previously exported dataset (.json, .jsonl, .csv). We'll apply linguistic rules to safely remove emojis, unwanted punctuations, URLs, non-Afan Oromoo posts, and very short posts.
                    </p>
                </div>

                {/* Upload Section */}
                <div className="max-w-2xl mx-auto mb-12">
                    <div className="flex items-center justify-center w-full">
                        <label htmlFor="dropzone-file" className={`flex flex-col items-center justify-center w-full h-48 border-2 border-dashed rounded-2xl cursor-pointer bg-gray-50 hover:bg-gray-100 transition-colors ${file ? 'border-emerald-400 bg-emerald-50/30' : 'border-gray-300'}`}>
                            <div className="flex flex-col items-center justify-center pt-5 pb-6">
                                <svg className={`w-10 h-10 mb-3 ${file ? 'text-emerald-500' : 'text-gray-400'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
                                </svg>
                                {file ? (
                                    <>
                                        <p className="mb-2 text-sm text-gray-700 font-semibold"><span className="text-emerald-600 border border-emerald-200 bg-emerald-100 rounded-md px-2 py-1">{file.name}</span></p>
                                        <p className="text-xs text-gray-500">Ready to clean</p>
                                    </>
                                ) : (
                                    <>
                                        <p className="mb-2 text-sm text-gray-500"><span className="font-semibold text-blue-600">Click to upload</span> or drag and drop</p>
                                        <p className="text-xs text-gray-500">JSON, JSONL, or CSV</p>
                                    </>
                                )}
                            </div>
                            <input id="dropzone-file" type="file" className="hidden" accept=".json,.jsonl,.csv" onChange={handleFileChange} />
                        </label>
                    </div>

                    <div className="mt-6 text-center">
                        <button
                            onClick={handleClean}
                            disabled={!file || isCleaning}
                            className={`w-full sm:w-auto px-8 py-3.5 font-semibold text-white rounded-xl shadow-sm transition-all duration-200 text-base
                            ${(!file || isCleaning) ? 'bg-emerald-300 cursor-not-allowed' : 'bg-emerald-600 hover:bg-emerald-700 active:scale-95 shadow-lg'}`}
                        >
                            {isCleaning ? (
                                <span className="flex items-center justify-center">
                                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                    Cleaning Dataset...
                                </span>
                            ) : (
                                'Clean Data'
                            )}
                        </button>
                    </div>
                </div>

                {/* Statistics & Export Section */}
                {stats && (
                    <div className="max-w-4xl mx-auto border-t border-gray-100 pt-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                        <h2 className="text-xl font-bold text-gray-800 mb-6 text-center">Cleaning Summary</h2>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                            <div className="bg-gray-50 rounded-xl p-5 border border-gray-200">
                                <p className="text-sm font-medium text-gray-500 mb-1">Original Posts</p>
                                <p className="text-2xl font-bold text-gray-900">{stats.original_posts}</p>
                                <span className="text-xs text-red-500 font-medium">-{stats.removed_posts} Removed</span>
                            </div>
                            <div className="bg-gray-50 rounded-xl p-5 border border-gray-200">
                                <p className="text-sm font-medium text-gray-500 mb-1">Final Posts</p>
                                <p className="text-2xl font-bold text-emerald-600">{stats.final_posts}</p>
                            </div>
                            <div className="bg-gray-50 rounded-xl p-5 border border-gray-200">
                                <p className="text-sm font-medium text-gray-500 mb-1">Original Comments</p>
                                <p className="text-2xl font-bold text-gray-900">{stats.original_comments}</p>
                                <span className="text-xs text-red-500 font-medium">-{stats.removed_comments} Removed</span>
                            </div>
                            <div className="bg-gray-50 rounded-xl p-5 border border-gray-200">
                                <p className="text-sm font-medium text-gray-500 mb-1">Final Comments</p>
                                <p className="text-2xl font-bold text-emerald-600">{stats.final_comments}</p>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-2 gap-4 mb-8">
                            <div className="bg-gray-50 rounded-xl p-5 border border-blue-200 bg-blue-50/30">
                                <p className="text-sm font-medium text-blue-600 mb-1">Original Tokens</p>
                                <p className="text-2xl font-bold text-blue-900">{stats.original_tokens?.toLocaleString() || 0}</p>
                                <span className="text-xs text-blue-500 font-medium">Before cleaning</span>
                            </div>
                            <div className="bg-gray-50 rounded-xl p-5 border border-emerald-200 bg-emerald-50/30">
                                <p className="text-sm font-medium text-emerald-600 mb-1">Final Valid Tokens</p>
                                <p className="text-2xl font-bold text-emerald-900">{stats.final_tokens?.toLocaleString() || 0}</p>
                                <span className="text-xs text-emerald-500 font-medium">Ready for dataset</span>
                            </div>
                        </div>

                        <div className="bg-emerald-50/50 rounded-xl p-6 border border-emerald-100 flex flex-col sm:flex-row items-center justify-between gap-6">
                            <div>
                                <h3 className="font-semibold text-emerald-900 mb-1">Ready to Export</h3>
                                <p className="text-emerald-700 text-sm">Download your freshly cleaned dataset in any format.</p>
                            </div>
                            <div className="flex gap-3">
                                <button onClick={() => handleExport('csv')} className="px-5 py-2.5 bg-white border border-gray-200 text-gray-700 font-medium rounded-lg shadow-sm hover:bg-gray-50 hover:text-emerald-600 hover:border-emerald-200 transition-all text-sm">
                                    CSV
                                </button>
                                <button onClick={() => handleExport('jsonl')} className="px-5 py-2.5 bg-white border border-gray-200 text-gray-700 font-medium rounded-lg shadow-sm hover:bg-gray-50 hover:text-emerald-600 hover:border-emerald-200 transition-all text-sm">
                                    JSONL
                                </button>
                                <button onClick={() => handleExport('json')} className="px-5 py-2.5 bg-emerald-600 text-white font-medium rounded-lg shadow-sm hover:bg-emerald-700 transition-all text-sm">
                                    JSON
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
