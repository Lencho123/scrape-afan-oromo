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