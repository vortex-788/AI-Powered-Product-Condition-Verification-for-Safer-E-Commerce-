import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import ScoreCircle from '../components/ScoreCircle';
import { getProducts } from '../services/api';

const statusColors = {
  verified: { bg: 'bg-green-500/10', text: 'text-green-400', dot: 'bg-green-500' },
  pending: { bg: 'bg-yellow-500/10', text: 'text-yellow-400', dot: 'bg-yellow-500' },
  flagged: { bg: 'bg-red-500/10', text: 'text-red-400', dot: 'bg-red-500' },
  returned: { bg: 'bg-purple-500/10', text: 'text-purple-400', dot: 'bg-purple-500' },
};

export default function Dashboard() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadProducts();
  }, []);

  const loadProducts = async () => {
    try {
      const res = await getProducts();
      setProducts(res.products || []);
    } catch (err) {
      console.error('Failed to load products:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredProducts = filter === 'all'
    ? products
    : products.filter(p => p.status === filter);

  const stats = {
    total: products.length,
    verified: products.filter(p => p.status === 'verified').length,
    flagged: products.filter(p => p.status === 'flagged').length,
    avgScore: products.length > 0
      ? Math.round(products.reduce((sum, p) => sum + (p.conditionScore || 0), 0) / products.length)
      : 0
  };

  return (
    <div className="pt-24 pb-16 min-h-screen">
      <div className="max-w-7xl mx-auto px-4">
        {/* Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-10">
          <div>
            <h1 className="text-3xl font-bold mb-1">
              <span className="gradient-text">Verification</span> Dashboard
            </h1>
            <p className="text-gray-400">Monitor and manage product condition verifications</p>
          </div>
          <Link to="/upload" className="btn-primary mt-4 sm:mt-0 flex items-center gap-2">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            New Verification
          </Link>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
          {[
            { label: 'Total Products', value: stats.total, icon: '📦', color: 'from-brand-500/20 to-brand-600/20' },
            { label: 'Verified', value: stats.verified, icon: '✅', color: 'from-green-500/20 to-green-600/20' },
            { label: 'Flagged', value: stats.flagged, icon: '🚩', color: 'from-red-500/20 to-red-600/20' },
            { label: 'Avg Score', value: stats.avgScore, icon: '⭐', color: 'from-yellow-500/20 to-yellow-600/20' },
          ].map((stat, i) => (
            <div key={i} className={`card bg-gradient-to-br ${stat.color}`}>
              <div className="flex items-center justify-between mb-3">
                <span className="text-2xl">{stat.icon}</span>
              </div>
              <div className="text-3xl font-bold text-white mb-1">{stat.value}</div>
              <div className="text-sm text-gray-400">{stat.label}</div>
            </div>
          ))}
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
          {['all', 'verified', 'pending', 'flagged', 'returned'].map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all
                ${filter === f ? 'bg-brand-600 text-white' : 'glass text-gray-400 hover:text-white'}`}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>

        {/* Product Table */}
        {loading ? (
          <div className="space-y-4">
            {[1,2,3].map(i => (
              <div key={i} className="card shimmer h-20" />
            ))}
          </div>
        ) : filteredProducts.length === 0 ? (
          <div className="card text-center py-16">
            <div className="text-5xl mb-4">📭</div>
            <h3 className="text-xl font-bold mb-2">No products found</h3>
            <p className="text-gray-400 mb-6">Start by verifying your first product</p>
            <Link to="/upload" className="btn-primary inline-flex items-center gap-2">
              Upload Product
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredProducts.map((product) => {
              const sc = statusColors[product.status] || statusColors.pending;
              return (
                <div key={product._id} className="card flex flex-col sm:flex-row items-start sm:items-center gap-4 hover:bg-white/5 group">
                  {/* Thumbnail */}
                  <div className="w-16 h-16 rounded-xl bg-surface-600 overflow-hidden flex-shrink-0">
                    {product.images?.[0]?.url ? (
                      <img src={product.images[0].url} alt="" className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-2xl">📷</div>
                    )}
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-1">
                      <h3 className="font-bold text-white truncate">{product.name}</h3>
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium ${sc.bg} ${sc.text}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${sc.dot}`} />
                        {product.status}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-gray-500">
                      <span className="capitalize">{product.category}</span>
                      <span>ID: {product.passportData?.digitalId || product.productId?.slice(0,8)}</span>
                      <span>{new Date(product.createdAt).toLocaleDateString()}</span>
                    </div>
                  </div>

                  {/* Score */}
                  <div className="flex items-center gap-4">
                    {product.conditionScore !== null && (
                      <ScoreCircle score={product.conditionScore} size={56} strokeWidth={4} label="" />
                    )}
                    <Link
                      to={`/passport?id=${product.productId || product._id}`}
                      className="text-brand-400 hover:text-brand-300 text-sm font-medium transition-colors opacity-0 group-hover:opacity-100"
                    >
                      View →
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
