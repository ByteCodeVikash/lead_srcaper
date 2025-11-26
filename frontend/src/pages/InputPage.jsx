import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, Settings, Info } from 'lucide-react';
import { jobsAPI } from '../services/api';

const InputPage = () => {
    const navigate = useNavigate();
    const [inputText, setInputText] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const onDrop = async (acceptedFiles) => {
        if (acceptedFiles.length === 0) return;

        const file = acceptedFiles[0];
        setLoading(true);
        setError(null);

        try {
            const job = await jobsAPI.createJobWithFile(file);
            navigate(`/jobs/${job.id}`);
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to upload file');
        } finally {
            setLoading(false);
        }
    };

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'text/csv': ['.csv'],
            'application/vnd.ms-excel': ['.xls'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
        },
        maxFiles: 1,
    });

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!inputText.trim()) {
            setError('Please enter at least one company name or URL');
            return;
        }

        setLoading(true);
        setError(null);

        try {
            // Split by comma or newline
            const companies = inputText
                .split(/[,\n]/)
                .map(c => c.trim())
                .filter(c => c);

            const job = await jobsAPI.createJob({ companies });
            navigate(`/jobs/${job.id}`);
        } catch (err) {
            setError(err.response?.data?.detail || 'Failed to create job');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-8">
            <div className="max-w-5xl mx-auto">
                {/* Header */}
                <div className="text-center mb-12">
                    <h1 className="text-5xl font-bold text-white mb-4">
                        RankRiseUSA <span className="text-primary-400">Web Scraper</span>
                    </h1>
                    <p className="text-gray-400 text-lg">
                        Extract contact information from company websites automatically
                    </p>
                </div>

                {/* Legal Notice */}
                <div className="bg-yellow-900/20 border border-yellow-700/50 rounded-lg p-4 mb-8 flex items-start gap-3">
                    <Info className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
                    <div className="text-sm text-yellow-200">
                        <strong>Legal Notice:</strong> This tool is for educational purposes only. Always respect robots.txt,
                        website terms of service, and applicable laws. Do not use for spam or unauthorized data collection.
                    </div>
                </div>

                <div className="grid md:grid-cols-2 gap-8">
                    {/* Text Input Method */}
                    <div className="card">
                        <div className="flex items-center gap-3 mb-4">
                            <FileText className="w-6 h-6 text-primary-400" />
                            <h2 className="text-2xl font-bold text-white">Text Input</h2>
                        </div>

                        <form onSubmit={handleSubmit}>
                            <div className="mb-4">
                                <label className="block text-sm font-medium text-gray-300 mb-2">
                                    Company Names or URLs
                                </label>
                                <textarea
                                    value={inputText}
                                    onChange={(e) => setInputText(e.target.value)}
                                    className="input h-64 resize-none font-mono text-sm"
                                    placeholder="Enter company names or URLs (comma or newline separated)&#10;&#10;Example:&#10;Google Inc&#10;https://microsoft.com&#10;Apple, Amazon, Tesla"
                                    disabled={loading}
                                />
                            </div>

                            {error && (
                                <div className="mb-4 p-3 bg-red-900/50 border border-red-700 rounded-lg text-red-200 text-sm">
                                    {error}
                                </div>
                            )}

                            <button
                                type="submit"
                                disabled={loading || !inputText.trim()}
                                className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {loading ? 'Creating Job...' : 'Start Scraping'}
                            </button>
                        </form>
                    </div>

                    {/* File Upload Method */}
                    <div className="card">
                        <div className="flex items-center gap-3 mb-4">
                            <Upload className="w-6 h-6 text-primary-400" />
                            <h2 className="text-2xl font-bold text-white">File Upload</h2>
                        </div>

                        <div
                            {...getRootProps()}
                            className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-all ${isDragActive
                                    ? 'border-primary-500 bg-primary-500/10'
                                    : 'border-gray-600 hover:border-primary-500 hover:bg-gray-700/50'
                                } ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
                        >
                            <input {...getInputProps()} disabled={loading} />

                            <Upload className="w-16 h-16 text-gray-400 mx-auto mb-4" />

                            {isDragActive ? (
                                <p className="text-primary-400 text-lg font-medium">
                                    Drop the file here...
                                </p>
                            ) : (
                                <>
                                    <p className="text-white text-lg font-medium mb-2">
                                        Drag & drop a CSV or Excel file
                                    </p>
                                    <p className="text-gray-400 text-sm mb-4">
                                        or click to browse
                                    </p>
                                    <p className="text-gray-500 text-xs">
                                        Supported formats: .csv, .xlsx, .xls
                                    </p>
                                </>
                            )}
                        </div>

                        {loading && (
                            <div className="mt-4 text-center text-gray-400">
                                Processing file...
                            </div>
                        )}
                    </div>
                </div>

                {/* Features Info */}
                <div className="mt-12 grid md:grid-cols-3 gap-6">
                    <div className="text-center">
                        <div className="w-12 h-12 bg-primary-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
                            <span className="text-2xl">🌐</span>
                        </div>
                        <h3 className="text-white font-semibold mb-1">Multi-Source</h3>
                        <p className="text-gray-400 text-sm">
                            Scrapes websites, Google Maps, LinkedIn, and directories
                        </p>
                    </div>

                    <div className="text-center">
                        <div className="w-12 h-12 bg-primary-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
                            <span className="text-2xl">📊</span>
                        </div>
                        <h3 className="text-white font-semibold mb-1">Smart Extraction</h3>
                        <p className="text-gray-400 text-sm">
                            Extracts phones, emails, social links with normalization
                        </p>
                    </div>

                    <div className="text-center">
                        <div className="w-12 h-12 bg-primary-500/20 rounded-full flex items-center justify-center mx-auto mb-3">
                            <span className="text-2xl">📥</span>
                        </div>
                        <h3 className="text-white font-semibold mb-1">Export Ready</h3>
                        <p className="text-gray-400 text-sm">
                            Download results in CSV, Excel, or ZIP formats
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default InputPage;
