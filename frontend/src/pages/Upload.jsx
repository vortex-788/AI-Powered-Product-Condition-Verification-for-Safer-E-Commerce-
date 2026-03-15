import { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import ScoreCircle from '../components/ScoreCircle';
import { createProduct, verifyImage, verifyVideo } from '../services/api';

export default function Upload() {
  const [mode, setMode] = useState('image'); // 'image' or 'video'
  const [files, setFiles] = useState([]);
  const [previews, setPreviews] = useState([]);
  const [productName, setProductName] = useState('');
  const [category, setCategory] = useState('electronics');
  const [isUploading, setIsUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef(null);
  const navigate = useNavigate();

  const handleFiles = useCallback((newFiles) => {
    const fileArray = Array.from(newFiles);
    setFiles(prev => [...prev, ...fileArray]);

    fileArray.forEach(f => {
      const url = URL.createObjectURL(f);
      setPreviews(prev => [...prev, { url, name: f.name, type: f.type }]);
    });
    setError('');
  }, []);

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files) handleFiles(e.dataTransfer.files);
  };

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
    setPreviews(prev => {
      URL.revokeObjectURL(prev[index].url);
      return prev.filter((_, i) => i !== index);
    });
  };

  const handleSubmit = async () => {
    if (files.length === 0) {
      setError('Please select at least one file');
      return;
    }

    setIsUploading(true);
    setError('');

    try {
      // First create the product
      const productForm = new FormData();
      productForm.append('name', productName || 'Unnamed Product');
      productForm.append('category', category);
      files.forEach(f => productForm.append('images', f));

      const productRes = await createProduct(productForm);
      const productId = productRes.product?._id;

      // Then run verification
      const verifyForm = new FormData();
      if (productId) verifyForm.append('productId', productId);

      if (mode === 'video') {
        verifyForm.append('video', files[0]);
        const verifyRes = await verifyVideo(verifyForm);
        setResult(verifyRes.verification);
      } else {
        files.forEach(f => verifyForm.append('images', f));
        const verifyRes = await verifyImage(verifyForm);
        setResult(verifyRes.verification);
      }
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Upload failed. Make sure the backend server is running.');
    } finally {
      setIsUploading(false);
    }
  };

  const resetForm = () => {
    setFiles([]);
    setPreviews([]);
    setResult(null);
    setError('');
    setProductName('');
  };

  return (
    <div className="pt-24 pb-16 min-h-screen">
      <div className="max-w-4xl mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-10">
          <h1 className="text-3xl sm:text-4xl font-bold mb-3">
            <span className="gradient-text">Verify Product</span> Condition
          </h1>
          <p className="text-gray-400">Upload product images or videos for AI-powered condition analysis</p>
        </div>

        {!result ? (
          <>
            {/* Mode Toggle */}
            <div className="flex justify-center mb-8">
              <div className="glass rounded-xl p-1 inline-flex">
                {['image', 'video'].map(m => (
                  <button
                    key={m}
                    onClick={() => { setMode(m); setFiles([]); setPreviews([]); }}
                    className={`px-6 py-2.5 rounded-lg text-sm font-medium transition-all duration-300
                      ${mode === m ? 'bg-brand-600 text-white shadow-lg shadow-brand-600/30' : 'text-gray-400 hover:text-white'}`}
                  >
                    {m === 'image' ? '📸 Image Scan' : '🎥 Video Scan'}
                  </button>
                ))}
              </div>
            </div>

            {/* Product Info */}
            <div className="grid sm:grid-cols-2 gap-4 mb-6">
              <div>
                <label className="block text-sm text-gray-400 mb-1.5">Product Name</label>
                <input
                  type="text"
                  value={productName}
                  onChange={e => setProductName(e.target.value)}
                  placeholder="e.g. MacBook Pro 14-inch"
                  className="w-full px-4 py-3 glass rounded-xl text-white placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-brand-500/50"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1.5">Category</label>
                <select
                  value={category}
                  onChange={e => setCategory(e.target.value)}
                  className="w-full px-4 py-3 glass rounded-xl text-white bg-transparent focus:outline-none focus:ring-2 focus:ring-brand-500/50"
                >
                  <option value="electronics">Electronics</option>
                  <option value="clothing">Clothing</option>
                  <option value="furniture">Furniture</option>
                  <option value="accessories">Accessories</option>
                  <option value="appliances">Appliances</option>
                  <option value="other">Other</option>
                </select>
              </div>
            </div>

            {/* Upload Zone */}
            <div
              className={`upload-zone rounded-2xl p-12 text-center cursor-pointer transition-all
                         ${dragActive ? 'dragging' : ''}`}
              onDrop={handleDrop}
              onDragOver={e => { e.preventDefault(); setDragActive(true); }}
              onDragLeave={() => setDragActive(false)}
              onClick={() => inputRef.current?.click()}
            >
              <input
                ref={inputRef}
                type="file"
                multiple={mode === 'image'}
                accept={mode === 'image' ? 'image/*' : 'video/*'}
                className="hidden"
                onChange={e => handleFiles(e.target.files)}
              />
              <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-brand-600/10 flex items-center justify-center">
                <svg className="w-8 h-8 text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                </svg>
              </div>
              <p className="text-lg font-medium text-white mb-1">
                {dragActive ? 'Drop files here' : `Drag & drop ${mode === 'image' ? 'images' : 'video'} here`}
              </p>
              <p className="text-sm text-gray-500">or click to browse • {mode === 'image' ? 'JPG, PNG, WebP' : 'MP4, MOV'}</p>
            </div>

            {/* File Previews */}
            {previews.length > 0 && (
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mt-6">
                {previews.map((p, i) => (
                  <div key={i} className="relative group rounded-xl overflow-hidden glass">
                    {p.type.startsWith('video') ? (
                      <video src={p.url} className="w-full h-32 object-cover" />
                    ) : (
                      <img src={p.url} alt={p.name} className="w-full h-32 object-cover" />
                    )}
                    <button
                      onClick={(e) => { e.stopPropagation(); removeFile(i); }}
                      className="absolute top-2 right-2 w-6 h-6 bg-red-500/80 rounded-full flex items-center justify-center
                               opacity-0 group-hover:opacity-100 transition-opacity text-white text-xs"
                    >
                      ✕
                    </button>
                    <div className="p-2 text-xs text-gray-400 truncate">{p.name}</div>
                  </div>
                ))}
              </div>
            )}

            {error && (
              <div className="mt-4 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                {error}
              </div>
            )}

            {/* Submit */}
            <div className="mt-8 text-center">
              <button
                onClick={handleSubmit}
                disabled={isUploading || files.length === 0}
                className="btn-primary text-lg px-12 py-4 disabled:opacity-50 disabled:cursor-not-allowed
                         inline-flex items-center gap-3"
              >
                {isUploading ? (
                  <>
                    <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Analyzing...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
                    </svg>
                    Verify Condition
                  </>
                )}
              </button>
            </div>
          </>
        ) : (
          /* Results View */
          <div className="animate-fade-in">
            <div className="card text-center mb-8">
              <h2 className="text-xl font-bold mb-6">Verification Complete</h2>
              <div className="flex justify-center mb-6">
                <ScoreCircle score={result.score} size={160} strokeWidth={10} label="Condition" />
              </div>
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold"
                style={{
                  backgroundColor: result.score >= 70 ? 'rgba(0,255,136,0.1)' : result.score >= 50 ? 'rgba(245,158,11,0.1)' : 'rgba(239,68,68,0.1)',
                  color: result.score >= 70 ? '#00ff88' : result.score >= 50 ? '#f59e0b' : '#ef4444'
                }}>
                {result.grade}
              </div>
              <p className="text-gray-400 text-sm mt-4">
                Processed in {result.processingTime} • {result.filesAnalyzed || result.framesAnalyzed || 1} files analyzed
              </p>
            </div>

            {/* Damages */}
            {result.damages && result.damages.length > 0 && (
              <div className="card mb-8">
                <h3 className="text-lg font-bold mb-4">Detected Issues</h3>
                <div className="space-y-3">
                  {result.damages.map((d, i) => (
                    <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-white/5">
                      <div className="flex items-center gap-3">
                        <div className={`w-2 h-2 rounded-full ${
                          d.severity === 'severe' ? 'bg-red-500' :
                          d.severity === 'moderate' ? 'bg-yellow-500' : 'bg-blue-500'
                        }`} />
                        <span className="font-medium capitalize">{d.type}</span>
                      </div>
                      <div className="flex items-center gap-4 text-sm">
                        <span className={`capitalize ${
                          d.severity === 'severe' ? 'text-red-400' :
                          d.severity === 'moderate' ? 'text-yellow-400' : 'text-blue-400'
                        }`}>{d.severity}</span>
                        <span className="text-gray-500">{Math.round((d.confidence || 0) * 100)}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button onClick={resetForm} className="btn-secondary">Verify Another</button>
              <button onClick={() => navigate('/dashboard')} className="btn-primary">View Dashboard</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
