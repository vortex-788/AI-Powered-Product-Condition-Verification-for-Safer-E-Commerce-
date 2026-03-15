import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Upload from './pages/Upload';
import Dashboard from './pages/Dashboard';
import Passport from './pages/Passport';
import FraudCheck from './pages/FraudCheck';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-surface-900">
        <Navbar />
        <main>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/passport" element={<Passport />} />
            <Route path="/fraud-check" element={<FraudCheck />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
