import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const jobsAPI = {
    // Create new job
    createJob: async (data) => {
        const response = await api.post('/api/jobs/', data);
        return response.data;
    },

    // Create job with file upload
    createJobWithFile: async (file) => {
        const formData = new FormData();
        formData.append('file', file);

        const response = await api.post('/api/jobs/', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    // List all jobs
    listJobs: async (skip = 0, limit = 100) => {
        const response = await api.get(`/api/jobs/?skip=${skip}&limit=${limit}`);
        return response.data;
    },

    // Get job by ID
    getJob: async (jobId) => {
        const response = await api.get(`/api/jobs/${jobId}`);
        return response.data;
    },

    // Get job status
    getJobStatus: async (jobId) => {
        const response = await api.get(`/api/jobs/${jobId}/status`);
        return response.data;
    },

    // Get job results
    getJobResults: async (jobId, skip = 0, limit = 1000) => {
        const response = await api.get(`/api/jobs/${jobId}/results?skip=${skip}&limit=${limit}`);
        return response.data;
    },

    // Get job summary
    getJobSummary: async (jobId) => {
        const response = await api.get(`/api/jobs/${jobId}/summary`);
        return response.data;
    },

    // Export endpoints
    exportCSV: (jobId) => `${API_BASE_URL}/api/jobs/${jobId}/export/csv`,
    exportExcel: (jobId) => `${API_BASE_URL}/api/jobs/${jobId}/export/xlsx`,
    exportZip: (jobId) => `${API_BASE_URL}/api/jobs/${jobId}/export/zip`,
};

export default api;
