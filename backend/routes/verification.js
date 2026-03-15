const express = require('express');
const router = express.Router();
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');
const path = require('path');
const Product = require('../models/Product');
const Verification = require('../models/Verification');
const upload = require('../middleware/upload');

const AI_SERVICE_URL = process.env.AI_SERVICE_URL || 'http://localhost:8000';

// POST /api/verify/image — Verify product via image
router.post('/image', upload.array('images', 10), async (req, res) => {
  try {
    const { productId } = req.body;
    const startTime = Date.now();

    // Find or validate product
    let product = null;
    if (productId) {
      product = await Product.findById(productId) || await Product.findOne({ productId });
    }

    // Analyze each image via AI service
    const analysisResults = [];

    for (const file of req.files) {
      try {
        const formData = new FormData();
        formData.append('file', fs.createReadStream(file.path));

        console.log(`[Backend] Sending image to AI Service at ${AI_SERVICE_URL}...`);
        const aiResponse = await axios.post(`${AI_SERVICE_URL}/analyze/image`, formData, {
          headers: formData.getHeaders(),
          timeout: 60000 // Give AI full time to analyze
        });
        console.log(`[Backend] AI Service responded successfully in ${Date.now() - startTime}ms`);
        analysisResults.push(aiResponse.data);
      } catch (aiError) {
        console.error(`[Backend] AI Service failed or timed out:`, aiError.message);
        throw new Error(`AI Analysis Failed: ${aiError.message}`);
      }
    }

    // Aggregate scores
    const avgScore = Math.round(
      analysisResults.reduce((sum, r) => sum + (r.condition_score || 75), 0) / analysisResults.length
    );

    // Determine grade
    let grade = 'Excellent';
    if (avgScore < 90) grade = 'Good';
    if (avgScore < 70) grade = 'Fair';
    if (avgScore < 50) grade = 'Poor';
    if (avgScore < 30) grade = 'Damaged';

    // Collect all damages
    const allDamages = analysisResults.flatMap(r => r.damages || []);

    // Save verification record
    const verification = new Verification({
      productId: product?._id,
      type: 'image',
      score: avgScore,
      grade,
      damages: allDamages,
      files: req.files.map(f => ({
        url: `/uploads/images/${f.filename}`,
        filename: f.filename,
        type: 'image'
      })),
      metadata: {
        processingTime: Date.now() - startTime,
        modelVersion: '1.0.0',
        aiServiceResponse: analysisResults
      }
    });
    await verification.save();

    // Update product if linked
    if (product) {
      product.conditionScore = avgScore;
      product.conditionGrade = grade;
      product.damageDetails = allDamages;
      product.status = avgScore >= 50 ? 'verified' : 'flagged';
      product.verificationHistory.push({
        verificationId: verification.verificationId,
        type: 'image',
        score: avgScore,
        performedAt: new Date()
      });
      product.passportData.verificationCount += 1;
      product.passportData.lastVerified = new Date();
      await product.save();
    }

    res.json({
      success: true,
      verification: {
        id: verification.verificationId,
        score: avgScore,
        grade,
        damages: allDamages,
        processingTime: `${Date.now() - startTime}ms`,
        filesAnalyzed: req.files.length
      }
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// POST /api/verify/video — Verify product via video
router.post('/video', upload.single('video'), async (req, res) => {
  try {
    const { productId } = req.body;
    const startTime = Date.now();

    let product = null;
    if (productId) {
      product = await Product.findById(productId) || await Product.findOne({ productId });
    }

    let aiResult;
    try {
      const formData = new FormData();
      formData.append('file', fs.createReadStream(req.file.path));

      console.log(`[Backend] Sending video to AI Service at ${AI_SERVICE_URL}...`);
      const aiResponse = await axios.post(`${AI_SERVICE_URL}/analyze/video`, formData, {
        headers: formData.getHeaders(),
        timeout: 60000
      });
      console.log(`[Backend] AI Service video response received in ${Date.now() - startTime}ms`);
      aiResult = aiResponse.data;
    } catch (aiError) {
      console.error(`[Backend] AI Video processing failed:`, aiError.message);
      throw new Error(`AI Video Analysis Failed: ${aiError.message}`);
    }

    const verification = new Verification({
      productId: product?._id,
      type: 'video',
      score: aiResult.condition_score,
      grade: aiResult.grade,
      damages: aiResult.damages || [],
      frameAnalysis: (aiResult.frame_results || []).map(f => ({
        frameNumber: f.frame_number,
        score: f.score,
        damages: f.damages || []
      })),
      files: [{
        url: `/uploads/videos/${req.file.filename}`,
        filename: req.file.filename,
        type: 'video'
      }],
      metadata: {
        processingTime: Date.now() - startTime,
        modelVersion: '1.0.0',
        aiServiceResponse: aiResult
      }
    });
    await verification.save();

    if (product) {
      product.conditionScore = aiResult.condition_score;
      product.conditionGrade = aiResult.grade;
      product.status = aiResult.condition_score >= 50 ? 'verified' : 'flagged';
      product.verificationHistory.push({
        verificationId: verification.verificationId,
        type: 'video',
        score: aiResult.condition_score,
        performedAt: new Date()
      });
      product.passportData.verificationCount += 1;
      product.passportData.lastVerified = new Date();
      await product.save();
    }

    res.json({
      success: true,
      verification: {
        id: verification.verificationId,
        score: aiResult.condition_score,
        grade: aiResult.grade,
        framesAnalyzed: aiResult.frames_analyzed,
        damages: aiResult.damages || [],
        processingTime: `${Date.now() - startTime}ms`
      }
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// GET /api/verify/:productId/history — Verification history
router.get('/:productId/history', async (req, res) => {
  try {
    const product = await Product.findById(req.params.productId) 
                   || await Product.findOne({ productId: req.params.productId });
    if (!product) return res.status(404).json({ success: false, error: 'Product not found' });

    const verifications = await Verification.find({ productId: product._id })
      .sort({ createdAt: -1 });

    res.json({ success: true, verifications });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

module.exports = router;
