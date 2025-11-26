import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Download, ArrowLeft, CheckCircle, XCircle, Clock, Loader } from 'lucide-react';
import { jobsAPI } from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';

const JobDetailPage = () => {
    const { jobId } = useParams();
    const [job, setJob] = useState(null);
    const [results, setResults] = useState([]);
    const [summary, setSummary] = useState(null);
    const [loading, setLoading] = useState(true);
    const { status: wsStatus } = useWebSocket(jobId);

    useEffect(() => {
        loadJob();
        loadResults();
        loadSummary();

        // Poll for updates every 3 seconds
        const interval = setInterval(() => {
            loadJob();
            if (job?.status === 'completed') {
                loadResults();
                loadSummary();
                clearInterval(interval);
            }
        }, 3000);

        return () => clearInterval(interval);
    }, [jobId]);

    const loadJob = async () => {
        try {
            const data = await jobsAPI.getJob(jobId);
            setJob(data);
        } catch (error) {
            console.error('Error loading job:', error);
        } finally {
            setLoading(false);
        }
    };

    const loadResults = async () => {
        try {
            const data = await jobsAPI.getJobResults(jobId);
            setResults(data);
        } catch (error) {
            console.error('Error loading results:', error);
        }
    };

    const loadSummary = async () => {
        try {
            const data = await jobsAPI.getJobSummary(jobId);
            setSummary(data);
        } catch (error) {
            console.error('Error loading summary:', error);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center">
                <Loader className="w-12 h-12 text-primary-500 animate-spin" />
            </div>
        );
    }

    if (!job) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-8">
                <div className="max-w-2xl mx-auto text-center">
                    <h1 className="text-3xl font-bold text-white mb-4">Job Not Found</h1>
                    <Link to="/" className="btn-primary">Go Back</Link>
                </div>
            </div>
        );
    }

    const progress = job.total_companies > 0
        ? (job.processed_companies / job.total_companies * 100).toFixed(1)
        : 0;

    const getStatusIcon = (status) => {
        switch (status) {
            case 'completed':
                return <CheckCircle className="w-6 h-6 text-green-500" />;
            case 'failed':
                return <XCircle className="w-6 h-6 text-red-500" />;
            case 'processing':
                return <Loader className="w-6 h-6 text-primary-500 animate-spin" />;
            default:
                return <Clock className="w-6 h-6 text-yellow-500" />;
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <Link to="/" className="inline-flex items-center gap-2 text-gray-400 hover:text-white mb-4">
                        <ArrowLeft className="w-4 h-4" />
                        Back to Home
                    </Link>

                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-4xl font-bold text-white mb-2">Job #{jobId}</h1>
                            <p className="text-gray-400">
                                Created {new Date(job.created_at).toLocaleString()}
                            </p>
                        </div>

                        <div className="flex items-center gap-3">
                            {getStatusIcon(job.status)}
                            <span className="text-white font-semibold capitalize">{job.status}</span>
                        </div>
                    </div>
                </div>

                {/* Progress Card */}
                <div className="card mb-8">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-xl font-bold text-white">Progress</h2>
                        <span className="text-2xl font-bold text-primary-400">{progress}%</span>
                    </div>

                    <div className="w-full bg-gray-700 rounded-full h-4 mb-4">
                        <div
                            className="bg-gradient-to-r from-primary-500 to-primary-600 h-4 rounded-full transition-all duration-300"
                            style={{ width: `${progress}%` }}
                        />
                    </div>

                    <div className="grid grid-cols-4 gap-4 text-center">
                        <div>
                            <div className="text-2xl font-bold text-white">{job.total_companies}</div>
                            <div className="text-sm text-gray-400">Total Companies</div>
                        </div>
                        <div>
                            <div className="text-2xl font-bold text-primary-400">{job.processed_companies}</div>
                            <div className="text-sm text-gray-400">Processed</div>
                        </div>
                        <div>
                            <div className="text-2xl font-bold text-green-400">{job.total_phones_found}</div>
                            <div className="text-sm text-gray-400">Phones Found</div>
                        </div>
                        <div>
                            <div className="text-2xl font-bold text-blue-400">{job.total_emails_found}</div>
                            <div className="text-sm text-gray-400">Emails Found</div>
                        </div>
                    </div>
                </div>

                {/* Summary Stats */}
                {summary && summary.total_companies_processed > 0 && (
                    <div className="grid md:grid-cols-3 gap-6 mb-8">
                        <div className="card">
                            <h3 className="text-lg font-semibold text-white mb-2">Success Rate</h3>
                            <div className="text-3xl font-bold text-green-400">
                                {((summary.companies_with_contact / summary.total_companies_processed) * 100).toFixed(1)}%
                            </div>
                            <p className="text-gray-400 text-sm">{summary.companies_with_contact} companies with contact info</p>
                        </div>

                        <div className="card">
                            <h3 className="text-lg font-semibold text-white mb-2">Avg. Confidence</h3>
                            <div className="text-3xl font-bold text-primary-400">
                                {summary.average_confidence_score}%
                            </div>
                            <p className="text-gray-400 text-sm">Based on data source quality</p>
                        </div>

                        <div className="card">
                            <h3 className="text-lg font-semibold text-white mb-2">No Contact</h3>
                            <div className="text-3xl font-bold text-red-400">
                                {summary.companies_with_no_contact}
                            </div>
                            <p className="text-gray-400 text-sm">Companies without contact info</p>
                        </div>
                    </div>
                )}

                {/* Export Buttons */}
                {job.status === 'completed' && results.length > 0 && (
                    <div className="card mb-8">
                        <h2 className="text-xl font-bold text-white mb-4">Export Results</h2>
                        <div className="flex gap-4">
                            <a
                                href={jobsAPI.exportCSV(jobId)}
                                download
                                className="btn-primary flex items-center gap-2"
                            >
                                <Download className="w-4 h-4" />
                                Download CSV
                            </a>
                            <a
                                href={jobsAPI.exportExcel(jobId)}
                                download
                                className="btn-secondary flex items-center gap-2"
                            >
                                <Download className="w-4 h-4" />
                                Download Excel
                            </a>
                            <a
                                href={jobsAPI.exportZip(jobId)}
                                download
                                className="btn-secondary flex items-center gap-2"
                            >
                                <Download className="w-4 h-4" />
                                Download ZIP Archive
                            </a>
                        </div>
                    </div>
                )}

                {/* Results Table */}
                {results.length > 0 && (
                    <div className="card">
                        <h2 className="text-xl font-bold text-white mb-4">Results ({results.length})</h2>
                        <div className="overflow-x-auto">
                            <table className="table">
                                <thead className="table-header">
                                    <tr>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Company</th>
                                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Website</th>
                                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-300 uppercase">Phones</th>
                                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-300 uppercase">Emails</th>
                                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-300 uppercase">Status</th>
                                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-300 uppercase">Confidence</th>
                                    </tr>
                                </thead>
                                <tbody className="bg-gray-800 divide-y divide-gray-700">
                                    {results.map((result) => (
                                        <tr key={result.id} className="table-row">
                                            <td className="px-4 py-3 text-sm text-white">
                                                {result.resolved_company_name || result.original_input}
                                            </td>
                                            <td className="px-4 py-3 text-sm">
                                                {result.resolved_website_url ? (
                                                    <a
                                                        href={result.resolved_website_url}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="text-primary-400 hover:underline"
                                                    >
                                                        {new URL(result.resolved_website_url).hostname}
                                                    </a>
                                                ) : (
                                                    <span className="text-gray-500">-</span>
                                                )}
                                            </td>
                                            <td className="px-4 py-3 text-sm text-center text-green-400 font-semibold">
                                                {result.number_of_unique_phone_numbers_found}
                                            </td>
                                            <td className="px-4 py-3 text-sm text-center text-blue-400 font-semibold">
                                                {result.number_of_unique_emails_found}
                                            </td>
                                            <td className="px-4 py-3 text-sm text-center">
                                                <span className="px-2 py-1 rounded-full text-xs bg-gray-700 text-gray-300">
                                                    {result.extraction_status.replace(/_/g, ' ')}
                                                </span>
                                            </td>
                                            <td className="px-4 py-3 text-sm text-center text-primary-400 font-semibold">
                                                {result.confidence_score.toFixed(0)}%
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default JobDetailPage;
