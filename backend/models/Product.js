const mongoose = require('mongoose');
const { v4: uuidv4 } = require('uuid');

const productSchema = new mongoose.Schema({
  productId: {
    type: String,
    default: () => uuidv4(),
    unique: true,
    index: true
  },
  name: {
    type: String,
    required: true,
    trim: true
  },
  category: {
    type: String,
    required: true,
    enum: ['electronics', 'clothing', 'furniture', 'accessories', 'appliances', 'other']
  },
  description: {
    type: String,
    default: ''
  },
  images: [{
    url: String,
    filename: String,
    uploadedAt: { type: Date, default: Date.now }
  }],
  conditionScore: {
    type: Number,
    min: 0,
    max: 100,
    default: null
  },
  conditionGrade: {
    type: String,
    enum: ['Excellent', 'Good', 'Fair', 'Poor', 'Damaged', null],
    default: null
  },
  damageDetails: [{
    type: { type: String },
    severity: { type: String, enum: ['minor', 'moderate', 'severe'] },
    location: mongoose.Schema.Types.Mixed,
    confidence: Number
  }],
  verificationHistory: [{
    verificationId: String,
    type: { type: String, enum: ['image', 'video'] },
    score: Number,
    performedAt: { type: Date, default: Date.now }
  }],
  passportData: {
    digitalId: String,
    createdAt: { type: Date, default: Date.now },
    verificationCount: { type: Number, default: 0 },
    lastVerified: Date,
    fraudChecks: { type: Number, default: 0 },
    trustScore: { type: Number, default: 100 }
  },
  status: {
    type: String,
    enum: ['pending', 'verified', 'flagged', 'returned'],
    default: 'pending'
  },
  seller: {
    name: String,
    id: String
  }
}, { timestamps: true });

// Auto-generate passport data on creation
productSchema.pre('save', function(next) {
  if (!this.passportData.digitalId) {
    this.passportData.digitalId = `VS-${this.productId.slice(0, 8).toUpperCase()}`;
  }
  next();
});

// Calculate condition grade from score
productSchema.methods.updateGrade = function() {
  if (this.conditionScore >= 90) this.conditionGrade = 'Excellent';
  else if (this.conditionScore >= 70) this.conditionGrade = 'Good';
  else if (this.conditionScore >= 50) this.conditionGrade = 'Fair';
  else if (this.conditionScore >= 30) this.conditionGrade = 'Poor';
  else this.conditionGrade = 'Damaged';
};

module.exports = mongoose.model('Product', productSchema);
