import { useState, useRef } from 'react';
import ScoreCircle from '../components/ScoreCircle';
import { checkFraud } from '../services/api';

export default function FraudCheck() {
  const [originalFiles, setOriginalFiles] = useState([]);
  const [returnedFiles, setReturnedFiles] = useState([]);
  const [origPreviews, setOrigPreviews] = useState([]);
  const [retPreviews, setRetPreviews] = useState([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const origRef = useRef(null);
  const retRef = useRef(null);

  const handleOriginal = (e) => {
    const files = Array.from(e.target.files);
    setOriginalFiles(files);
    setOrigPreviews(files.map(f => URL.createObjectURL(f)));
  };

  const handleReturned = (e) => {
    const files = Array.from(e.target.files);
    setReturnedFiles(files);
    setRetPreviews(files.map(f => URL.createObjectURL(f)));
  };

  const runCheck = async () => {
    if (!originalFiles.length || !returnedFiles.length) {
      setError('Please upload both original and returned product images');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const form = new FormData();
      originalFiles.forEach(f => form.append('originalImages', f));
      returnedFiles.forEach(f => form.append('returnedImages', f));
      const res = await checkFraud(form);
      setResult(res.fraudCheck);
    } catch (err) {
      setError(err.response?.data?.error || 'Fraud check failed. Ensure backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const riskColors = {
    low: { bg: 'bg-green-500/10', text: 'text-green-400', border: 'border-green-500/30' },
    medium: { bg: 'bg-yellow-500/10', text: 'text-yellow-400', border: 'border-yellow-500/30' },
    high: { bg: 'bg-orange-500/10', text: 'text-orange-400', border: 'border-orange-500/30' },
    critical: { bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500/30' },
  };

  const reset = () => { setResult(null); setOriginalFiles([]); setReturnedFiles([]); setOrigPreviews([]); setRetPreviews([]); setError(''); };

  return (
    <div className="pt-24 pb-16 min-h-screen">
      <div className="max-w-5xl mx-auto px-4">
        <div className="text-center mb-10">
          <h1 className="text-3xl sm:text-4xl font-bold mb-3"><span className="gradient-text-warm">Return Fraud</span> Detection</h1>
          <p className="text-gray-400">Compare original vs returned product images to detect swaps and tampering</p>
        </div>

        {!result ? (
          <div className="space-y-8">
            {/* Side by Side Upload */}
            <div className="grid md:grid-cols-2 gap-6">
              {/* Original */}
              <div className="card">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-green-500" /> Original Product
                </h3>
                <div className="upload-zone rounded-xl p-8 text-center cursor-pointer" onClick={() => origRef.current?.click()}>
                  <input ref={origRef} type="file" multiple accept="image/*" className="hidden" onChange={handleOriginal} />
                  {origPreviews.length > 0 ? (
                    <div className="grid grid-cols-2 gap-2">
                      {origPreviews.map((p, i) => <img key={i} src={p} alt="" className="w-full h-24 object-cover rounded-lg" />)}
                    </div>
                  ) : (
                    <>
                      <div className="text-3xl mb-2">📸</div>
                      <p className="text-sm text-gray-400">Upload original product images</p>
                    </>
                  )}
                </div>
              </div>

              {/* Returned */}
              <div className="card">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                  <span className="w-3 h-3 rounded-full bg-red-500" /> Returned Product
                </h3>
                <div className="upload-zone rounded-xl p-8 text-center cursor-pointer" onClick={() => retRef.current?.click()}>
                  <input ref={retRef} type="file" multiple accept="image/*" className="hidden" onChange={handleReturned} />
                  {retPreviews.length > 0 ? (
                    <div className="grid grid-cols-2 gap-2">
                      {retPreviews.map((p, i) => <img key={i} src={p} alt="" className="w-full h-24 object-cover rounded-lg" />)}
                    </div>
                  ) : (
                    <>
                      <div className="text-3xl mb-2">🔄</div>
                      <p className="text-sm text-gray-400">Upload returned product images</p>
                    </>
                  )}
                </div>
              </div>
            </div>

            {error && <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">{error}</div>}

            <div className="text-center">
              <button onClick={runCheck} disabled={loading} className="btn-primary text-lg px-12 py-4 inline-flex items-center gap-3 disabled:opacity-50">
                {loading ? (
                  <><svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>Analyzing...</>
                ) : '🔍 Run Fraud Analysis'}
              </button>
            </div>
          </div>
        ) : (
          <div className="animate-fade-in space-y-6">
            {/* Result Header */}
            <div className={`card border ${result.fraudDetected ? 'border-red-500/30 bg-red-500/5' : 'border-green-500/30 bg-green-500/5'}`}>
              <div className="flex flex-col sm:flex-row items-center gap-6">
                <ScoreCircle score={Math.round(result.similarityScore)} size={120} strokeWidth={8} label="Similarity" />
                <div className="flex-1 text-center sm:text-left">
                  <div className={`text-2xl font-bold mb-1 ${result.fraudDetected ? 'text-red-400' : 'text-green-400'}`}>
                    {result.fraudDetected ? '⚠️ Fraud Detected' : '✅ No Fraud Detected'}
                  </div>
                  <div className="text-gray-400 mb-3">{result.recommendation}</div>
                  <div className="flex flex-wrap gap-3">
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${riskColors[result.riskLevel]?.bg} ${riskColors[result.riskLevel]?.text}`}>
                      Risk: {result.riskLevel?.toUpperCase()}
                    </span>
                    <span className="px-3 py-1 rounded-full text-xs font-semibold bg-white/5 text-gray-300 capitalize">
                      Type: {result.fraudType?.replace('_', ' ')}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Analysis Breakdown */}
            <div className="card">
              <h3 className="text-lg font-bold mb-4">Analysis Breakdown</h3>
              <div className="space-y-4">
                {[
                  ['Structural Similarity (SSIM)', result.details?.structuralSimilarity],
                  ['Feature Match (ORB)', result.details?.featureMatchScore],
                  ['Color Histogram', result.details?.colorHistogramMatch],
                  ['Texture Analysis', result.details?.textureAnalysis],
                ].map(([label, val], i) => (
                  <div key={i}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-400">{label}</span>
                      <span className="font-mono font-bold">{val != null ? `${Math.round(val)}%` : 'N/A'}</span>
                    </div>
                    <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                      <div className="h-full rounded-full transition-all duration-1000"
                        style={{
                          width: `${val || 0}%`,
                          background: val >= 70 ? 'linear-gradient(90deg, #00ff88, #00d4ff)' : val >= 40 ? 'linear-gradient(90deg, #f59e0b, #f97316)' : 'linear-gradient(90deg, #ef4444, #dc2626)'
                        }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Anomalies */}
            {result.details?.anomalies?.length > 0 && (
              <div className="card">
                <h3 className="text-lg font-bold mb-4">Anomalies Found</h3>
                <ul className="space-y-2">
                  {result.details.anomalies.map((a, i) => (
                    <li key={i} className="flex items-start gap-3 p-3 rounded-lg bg-red-500/5">
                      <span className="text-red-400 mt-0.5">⚠</span>
                      <span className="text-gray-300 text-sm">{a}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="text-center">
              <button onClick={reset} className="btn-secondary">Run Another Check</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
