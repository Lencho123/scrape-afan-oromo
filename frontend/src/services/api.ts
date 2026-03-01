import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000/api',
});

export const triggerScrape = (url: string) => api.post('/scrape', { url });

export const getPosts = (startDate?: string, endDate?: string, skip = 0, limit = 20) => {
    // Clean params: only include them if they have a value
    const params: any = { skip, limit };
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    
    return api.get('/posts', { params });
};

export const getPost = (postId: string) => api.get(`/posts/${postId}`);

export const updatePost = (postId: string, data: any) => api.put(`/posts/${postId}`, data);

export const deletePost = (postId: string) => api.delete(`/posts/${postId}`);

export const getStats = () => api.get('/stats');

export const downloadExport = async (format: string, startDate?: string, endDate?: string) => {
    const params: any = { format };
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;

    try {
        const response = await api.get('/export', {
            params,
            responseType: 'blob', // Required for file downloads
        });

        // Create the file blob
        const blobUrl = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = blobUrl;

        const extension = format === 'jsonl' ? 'jsonl' : format;
        const fileName = `facebook_data_${new Date().toISOString().split('T')[0]}.${extension}`;
        
        link.setAttribute('download', fileName);
        document.body.appendChild(link);
        link.click();

        // CLEANUP: 
        // 1. Remove the element from DOM
        link.parentNode?.removeChild(link);
        // 2. Free up memory by revoking the blob URL
        window.URL.revokeObjectURL(blobUrl); 
        
    } catch (error) {
        console.error("Export failed:", error);
        throw error; // Re-throw so the UI can show a toast error
    }
};