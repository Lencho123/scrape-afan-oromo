import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const api = axios.create({
    baseURL: BASE_URL,
});

api.interceptors.request.use((config) => {
    const token = localStorage.getItem('admin_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export const triggerScrape = (url: string) => api.post('/scrape', { url });

export const verifyPassword = async (password: string) => {
    const response = await api.post('/auth/verify', { password });
    return response.data;
};

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
            responseType: 'blob',
        });

        // Determine the correct MIME type
        const mimeTypes: Record<string, string> = {
            csv: 'text/csv;charset=utf-8',
            json: 'application/json',
            jsonl: 'application/x-ndjson',
        };

        // Standard Handling for CSV encoding (Excel Fix)
        let blobData = [response.data];
        if (format === 'csv') {
            // Prepend UTF-8 BOM so Excel recognizes the Oromo characters
            blobData = ["\ufeff", response.data];
        }

        const blob = new Blob(blobData, { type: mimeTypes[format] || 'application/octet-stream' });
        const blobUrl = window.URL.createObjectURL(blob);

        const link = document.createElement('a');
        link.href = blobUrl;

        // Standardized naming convention
        const dateStr = new Date().toISOString().split('T')[0];
        const fileName = `fb_export_${dateStr}.${format === 'jsonl' ? 'jsonl' : format}`;

        link.setAttribute('download', fileName);
        document.body.appendChild(link);
        link.click();

        // Standard Cleanup
        document.body.removeChild(link);
        window.URL.revokeObjectURL(blobUrl);

    } catch (error) {
        console.error("Export failed:", error);
        throw error;
    }
};

export const uploadForCleaning = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/clean-data', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });

    return response.data;
};