const mongoose = require('mongoose');
const { v4: uuidv4 } = require('uuid');

const fraudCheckSchema = new mongoose.Schema({
  checkId: {
    type: String,
    default: () => uuidv4(),
    unique: true
  },
  productId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Product',
    required: false
  },
  originalImages: [{
    url: String,
    filename: String
  }],
  returnedImages: [{
    url: String,
    filename: String
  }],
  similarityScore: {
    type: Number,
    min: 0,
    max: 100
  },
  fraudDetected: {
    type: Boolean,
    default: false
  },
  fraudType: {
    type: String,
    enum: ['none', 'product_swap', 'damage_added', 'different_model', 'tampered'],
    default: 'none'
  },
  riskLevel: {
    type: String,
    enum: ['low', 'medium', 'high', 'critical'],
    default: 'low'
  },
  details: {
    structuralSimilarity: Number,
    featureMatchScore: Number,
    colorHistogramMatch: Number,
    textureAnalysis: Number,
    anomalies: [String]
  },
  recommendation: {
    type: String,
    default: ''
  }
}, { timestamps: true });

module.exports = mongoose.model('FraudCheck', fraudCheckSchema);
