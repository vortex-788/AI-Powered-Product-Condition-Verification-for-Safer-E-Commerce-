import { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import ScoreCircle from '../components/ScoreCircle';
import { getProductPassport, getProducts } from '../services/api';

export default function Passport() {
  const [searchParams] = useSearchParams();
  const [passport, setPassport] = useState(null);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState(searchParams.get('id') || '');

  useEffect(() => { loadProducts(); }, []);
  useEffect(() => { if (selectedId) loadPassport(selectedId); }, [selectedId]);

  const loadProducts = async () => {
    try {
      const res = await getProducts();
      setProducts(res.products || []);
      if (!selectedId && res.products?.length > 0)
        setSelectedId(res.products[0].productId || res.products[0]._id);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const loadPassport = async (id) => {
    try { const res = await getProductPassport(id); setPassport(res.passport); }
    catch (err) { console.error(err); }
  };

  const gradeColor = (g) => {
    const m = { Excellent:'score-excellent', Good:'score-good', Fair:'score-fair', Poor:'score-poor', Damaged:'score-damaged' };
    return m[g] || 'text-gray-400';
  };

  if (loading) return <div className="pt-24 pb-16 min-h-screen"><div className="max-w-5xl mx-auto px-4"><div className="card shimmer h-64" /></div></div>;

  return (
    <div className="pt-24 pb-16 min-h-screen">
      <div className="max-w-5xl mx-auto px-4">
        <div className="text-center mb-10">
          <h1 className="text-3xl sm:text-4xl font-bold mb-3"><span className="gradient-text">Digital Product</span> Passport</h1>
          <p className="text-gray-400">Complete lifecycle and verification history</p>
        </div>

        {products.length > 0 && (
          <div className="mb-8">
            <select value={selectedId} onChange={e => setSelectedId(e.target.value)}
              className="w-full max-w-md px-4 py-3 glass rounded-xl text-white bg-transparent focus:outline-none focus:ring-2 focus:ring-brand-500/50">
              {products.map(p => <option key={p._id} value={p.productId || p._id} className="bg-surface-800">{p.name} — {p.passportData?.digitalId}</option>)}
            </select>
          </div>
        )}

        {!passport ? (
          <div className="card text-center py-16">
            <div className="text-5xl mb-4">🛂</div>
            <h3 className="text-xl font-bold mb-2">No Passport Found</h3>
            <p className="text-gray-400 mb-6">Verify a product first to generate its digital passport</p>
            <Link to="/upload" className="btn-primary">Verify Product</Link>
          </div>
        ) : (
          <div className="animate-fade-in space-y-8">
            {/* Passport Card */}
            <div className="card relative overflow-hidden">
              <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-brand-500 via-neon-blue to-neon-green" />
              <div className="flex flex-col md:flex-row items-start md:items-center gap-8 pt-4">
                <ScoreCircle score={passport.conditionScore || 0} size={140} strokeWidth={8} label="Condition" />
                <div className="flex-1 grid grid-cols-2 gap-4">
                  {[
                    ['Digital ID', <span className="font-mono text-brand-400 font-bold">{passport.digitalId}</span>],
                    ['Product', passport.productName],
                    ['Category', <span className="capitalize">{passport.category}</span>],
                    ['Grade', <span className={`font-bold ${gradeColor(passport.conditionGrade)}`}>{passport.conditionGrade || 'Pending'}</span>],
                    ['Status', <span className="capitalize">{passport.status}</span>],
                    ['Trust Score', <span className="font-bold text-neon-blue">{passport.passportData?.trustScore ?? 100}/100</span>],
                  ].map(([label, val], i) => (
                    <div key={i}><div className="text-xs text-gray-500 uppercase tracking-wider mb-1">{label}</div><div>{val}</div></div>
                  ))}
                </div>
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4">
              {[
                [passport.passportData?.verificationCount || 0, 'Verifications', 'text-brand-400'],
                [passport.passportData?.fraudChecks || 0, 'Fraud Checks', 'text-neon-blue'],
                [passport.lastVerified ? new Date(passport.lastVerified).toLocaleDateString() : 'Never', 'Last Verified', 'text-neon-green'],
              ].map(([v, l, c], i) => (
                <div key={i} className="card text-center"><div className={`text-2xl font-bold ${c}`}>{v}</div><div className="text-xs text-gray-500 mt-1">{l}</div></div>
              ))}
            </div>

            {/* Damages */}
            {passport.damageDetails?.length > 0 && (
              <div className="card">
                <h3 className="text-lg font-bold mb-4">Damage Report</h3>
                <div className="space-y-2">
                  {passport.damageDetails.map((d, i) => (
                    <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-white/5">
                      <div className="flex items-center gap-3">
                        <span className={`w-2 h-2 rounded-full ${d.severity === 'severe' ? 'bg-red-500' : d.severity === 'moderate' ? 'bg-yellow-500' : 'bg-blue-500'}`} />
                        <span className="capitalize font-medium">{d.type}</span>
                      </div>
                      <span className="text-sm text-gray-500 capitalize">{d.severity}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Timeline */}
            {passport.verificationHistory?.length > 0 && (
              <div className="card">
                <h3 className="text-lg font-bold mb-4">Verification Timeline</h3>
                <div className="space-y-4">
                  {passport.verificationHistory.map((v, i) => (
                    <div key={i} className="flex items-start gap-4">
                      <div className="w-3 h-3 rounded-full bg-brand-500 mt-1 flex-shrink-0" />
                      <div>
                        <div className="font-medium capitalize">{v.type} Verification</div>
                        <div className="text-sm text-gray-400">Score: <span className="text-brand-400 font-bold">{v.score}</span> • {new Date(v.performedAt).toLocaleString()}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
