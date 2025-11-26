import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import InputPage from './pages/InputPage';
import JobDetailPage from './pages/JobDetailPage';

function App() {
    return (
        <Router>
            <Routes>
                <Route path="/" element={<InputPage />} />
                <Route path="/jobs/:jobId" element={<JobDetailPage />} />
            </Routes>
        </Router>
    );
}

export default App;
