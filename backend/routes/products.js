const express = require('express');
const router = express.Router();
const Product = require('../models/Product');
const upload = require('../middleware/upload');

// POST /api/products — Create a new product
router.post('/', upload.array('images', 10), async (req, res) => {
  try {
    const { name, category, description, sellerName, sellerId } = req.body;

    const images = (req.files || []).map(file => ({
      url: `/uploads/images/${file.filename}`,
      filename: file.filename,
      uploadedAt: new Date()
    }));

    const product = new Product({
      name,
      category: category || 'other',
      description,
      images,
      seller: { name: sellerName, id: sellerId },
      passportData: {
        createdAt: new Date(),
        verificationCount: 0,
        fraudChecks: 0,
        trustScore: 100
      }
    });

    await product.save();

    res.status(201).json({
      success: true,
      message: 'Product created successfully',
      product
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// GET /api/products — List all products
router.get('/', async (req, res) => {
  try {
    const { status, category, page = 1, limit = 20 } = req.query;
    const filter = {};
    if (status) filter.status = status;
    if (category) filter.category = category;

    const products = await Product.find(filter)
      .sort({ createdAt: -1 })
      .skip((page - 1) * limit)
      .limit(parseInt(limit));

    const total = await Product.countDocuments(filter);

    res.json({
      success: true,
      products,
      pagination: { page: parseInt(page), limit: parseInt(limit), total, pages: Math.ceil(total / limit) }
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// GET /api/products/:id — Get product details
router.get('/:id', async (req, res) => {
  try {
    const product = await Product.findOne({ productId: req.params.id }) 
                   || await Product.findById(req.params.id);
    if (!product) return res.status(404).json({ success: false, error: 'Product not found' });
    res.json({ success: true, product });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// GET /api/products/:id/passport — Digital product passport
router.get('/:id/passport', async (req, res) => {
  try {
    const product = await Product.findOne({ productId: req.params.id })
                   || await Product.findById(req.params.id);
    if (!product) return res.status(404).json({ success: false, error: 'Product not found' });

    const passport = {
      digitalId: product.passportData.digitalId,
      productName: product.name,
      category: product.category,
      conditionScore: product.conditionScore,
      conditionGrade: product.conditionGrade,
      images: product.images,
      damageDetails: product.damageDetails,
      verificationHistory: product.verificationHistory,
      passportData: product.passportData,
      status: product.status,
      createdAt: product.createdAt,
      lastVerified: product.passportData.lastVerified
    };

    res.json({ success: true, passport });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

module.exports = router;
