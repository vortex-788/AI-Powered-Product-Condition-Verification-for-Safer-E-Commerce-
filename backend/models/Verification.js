const mongoose = require('mongoose');
const { v4: uuidv4 } = require('uuid');

const verificationSchema = new mongoose.Schema({
  verificationId: {
    type: String,
    default: () => uuidv4(),
    unique: true
  },
  productId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Product',
    required: true
  },
  type: {
    type: String,
    enum: ['image', 'video'],
    required: true
  },
  score: {
    type: Number,
    min: 0,
    max: 100
  },
  grade: {
    type: String,
    enum: ['Excellent', 'Good', 'Fair', 'Poor', 'Damaged']
  },
  damages: [{
    type: { type: String },
    severity: String,
    location: mongoose.Schema.Types.Mixed,
    confidence: Number,
    boundingBox: {
      x: Number,
      y: Number,
      width: Number,
      height: Number
    }
  }],
  frameAnalysis: [{
    frameNumber: Number,
    timestamp: Number,
    score: Number,
    damages: [{
      type: { type: String },
      severity: String,
      confidence: Number
    }]
  }],
  files: [{
    url: String,
    filename: String,
    type: { type: String }
  }],
  metadata: {
    processingTime: Number,
    modelVersion: String,
    aiServiceResponse: Object
  }
}, { timestamps: true });

module.exports = mongoose.model('Verification', verificationSchema);
