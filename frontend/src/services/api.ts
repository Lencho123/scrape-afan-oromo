import axios from 'axios';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
});

export const triggerScrape = (url: string) => api.post('/scrape', { url });

export const getPosts = (startDate?: string, endDate?: string, skip = 0, limit = 20) => {
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

    const response = await api.get('/export', {
        params,
        responseType: 'blob',
    });

    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;

    const extension = format === 'jsonl' ? 'jsonl' : format;
    link.setAttribute('download', `export_${new Date().toISOString().split('T')[0]}.${extension}`);

    document.body.appendChild(link);
    link.click();
    link.parentNode?.removeChild(link);
};
