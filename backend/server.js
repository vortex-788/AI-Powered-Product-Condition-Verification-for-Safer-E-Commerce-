const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const path = require('path');
require('dotenv').config();

const app = express();

// Middleware
app.use(cors());
app.use(express.json());
const os = require('os');
const uploadDir = path.join(os.tmpdir(), 'verishield-uploads');
app.use('/uploads', express.static(uploadDir));

// MongoDB Connection
mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/verishield')
  .then(() => console.log('✅ MongoDB connected'))
  .catch(err => console.error('❌ MongoDB connection error:', err));

// Routes
app.use('/api/products', require('./routes/products'));
app.use('/api/verify', require('./routes/verification'));
app.use('/api/fraud', require('./routes/fraud'));

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', service: 'VeriShield Backend', timestamp: new Date() });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Something went wrong!', message: err.message });
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`🚀 VeriShield Backend running on port ${PORT}`);
});

module.exports = app;
