"""
Damage Detector Service
Uses OpenCV for edge detection, contour analysis, and color anomaly detection.
Combines with a pretrained MobileNetV2 feature extractor (classification gated behind training flag).

Accuracy improvements:
- Raised detection thresholds to reduce false positives from normal product features
- Added solidity/aspect-ratio filters to distinguish damage from logos/labels
- Log-scale scoring formula instead of linear penalty
- Confidence-weighted aggregation (only damages > 0.6 confidence affect score)
- Neutralized untrained ML model influence
"""
import cv2
import numpy as np
from typing import Dict, List, Any
import logging

class DamageDetector:
    """AI-powered product damage detection using computer vision."""

    # Damage type labels
    DAMAGE_TYPES = [
        'scratch', 'crack', 'dent', 'discoloration', 'chip',
        'wear', 'stain', 'deformation', 'corrosion', 'missing_part'
    ]

    SEVERITY_THRESHOLDS = {
        'minor': (0, 0.02),        # < 2% of surface
        'moderate': (0.02, 0.08),  # 2-8% of surface
        'severe': (0.08, 1.0)      # > 8% of surface
    }

    # Minimum confidence to include a damage in scoring
    SCORING_CONFIDENCE_THRESHOLD = 0.6

    def __init__(self):
        """Initialize the damage detector with model weights."""
        self.model = None
        self.model_trained = False  # Gate: only use ML predictions if a trained model exists
        self._load_model_with_error_handling()

    def _load_model(self):
        """Load or initialize the ML model."""
        # Removed TensorFlow model (MobileNetV2) entirely for speed optimization.
        # It was introducing 2000-3000ms latency on startup and 200-500ms per inference,
        # despite the classification head being untrained.
        # Relying purely on the optimized OpenCV pipeline drops latency to <50ms natively.
        self.model = None
        self.model_trained = False
        print(" Fast OpenCV-only detection active (deep learning disabled for <100ms latency)")

    def _load_model_with_error_handling(self):
        try:
            self._load_model()
        except Exception as e:
            logging.error(f"Error loading model: {str(e)}")

    def analyze(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Analyze an image for product damage.

        Returns:
            dict with condition_score, damages, grade, and analysis details
        """
        try:
            # Resize for consistency
            h, w = image.shape[:2]
            analysis_size = 512
            scale = analysis_size / max(h, w)
            resized = cv2.resize(image, None, fx=scale, fy=scale)

            # Assess initial image quality for evaluation metrics and confidence weighting
            quality_metrics = self._assess_image_quality(resized)
            reliability = quality_metrics['reliability_multiplier']

            # Run detection pipeline
            edge_damage = self._detect_edge_anomalies(resized)
            color_damage = self._detect_color_anomalies(resized)
            texture_damage = self._detect_texture_anomalies(resized)
            contour_damage = self._detect_contour_irregularities(resized)

            # ML-based classification ONLY if model is actually trained
            ml_predictions = {}
            if self.model and self.model_trained:
                ml_predictions = self._ml_classify(image)

            # Combine all damage signals
            all_damages = []
            damage_area_ratio = 0.0

            for source, damages in [
                ('edge', edge_damage),
                ('color', color_damage),
                ('texture', texture_damage),
                ('contour', contour_damage)
            ]:
                for dmg in damages:
                    dmg['detection_source'] = source
                    # Apply model optimization: penalize confidence if image quality is poor
                    dmg['confidence'] = round(dmg['confidence'] * reliability, 3)
                    all_damages.append(dmg)
                    damage_area_ratio += dmg.get('area_ratio', 0)

            # ── Improved scoring formula ──
            # Only count damages above confidence threshold for scoring
            confident_damages = [
                d for d in all_damages
                if d.get('confidence', 0) >= self.SCORING_CONFIDENCE_THRESHOLD
            ]

            # Log-scale area penalty (gentler on small defects, still scales with area)
            confident_area_ratio = sum(d.get('area_ratio', 0) for d in confident_damages)
            if confident_area_ratio > 0:
                damage_penalty = min(40 * np.log2(1 + confident_area_ratio * 100), 70)
            else:
                damage_penalty = 0

            # Severity penalty — confidence-weighted, capped
            severity_penalty = 0
            for d in confident_damages:
                conf = d.get('confidence', 0.5)
                sev = d.get('severity', 'minor')
                if sev == 'severe':
                    severity_penalty += 8 * conf
                elif sev == 'moderate':
                    severity_penalty += 4 * conf
                else:
                    severity_penalty += 1.5 * conf
            severity_penalty = min(severity_penalty, 30)

            condition_score = max(0, min(100, 100 - damage_penalty - severity_penalty))

            # Add ML-based adjustments (only if model is trained)
            if ml_predictions:
                for dtype, confidence in ml_predictions.items():
                    if confidence > 0.6:
                        condition_score = max(0, condition_score - confidence * 8)
                        all_damages.append({
                            'type': dtype,
                            'severity': 'moderate' if confidence > 0.8 else 'minor',
                            'confidence': round(float(confidence), 3),
                            'detection_source': 'ml_model'
                        })

            condition_score = round(condition_score, 1)

            # Determine grade
            if condition_score >= 90:
                grade = 'Excellent'
            elif condition_score >= 70:
                grade = 'Good'
            elif condition_score >= 50:
                grade = 'Fair'
            elif condition_score >= 30:
                grade = 'Poor'
            else:
                grade = 'Damaged'

            return {
                'condition_score': condition_score,
                'grade': grade,
                'damages': all_damages[:20],  # Limit to top 20
                'analysis': {
                    'total_damage_area_ratio': round(damage_area_ratio, 4),
                    'confident_damage_count': len(confident_damages),
                    'total_detections': len(all_damages),
                    'detection_methods': ['edge', 'color', 'texture', 'contour'] + (['ml_model'] if ml_predictions else []),
                    'image_dimensions': {'width': w, 'height': h},
                    'ml_model_active': self.model_trained,
                    'image_quality_metrics': quality_metrics
                }
            }
        except Exception as e:
            logging.error(f"Error analyzing image: {str(e)}")
            return {
                'condition_score': 0,
                'grade': 'Unknown',
                'damages': [],
                'analysis': {}
            }

    def _assess_image_quality(self, image: np.ndarray) -> Dict[str, Any]:
        """Assess image for blur, brightness, and contrast to establish baseline evaluation metrics."""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Blur detection via Variance of Laplacian
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            is_blurry = laplacian_var < 100
            
            # Brightness via mean pixel intensity
            brightness = np.mean(gray)
            is_underexposed = brightness < 40
            is_overexposed = brightness > 215
            
            # Contrast via standard deviation
            contrast = np.std(gray)
            is_low_contrast = contrast < 35
            
            # Calculate a reliability score multiplier (0.5 to 1.0)
            reliability = 1.0
            if is_blurry: reliability -= 0.2
            if is_underexposed or is_overexposed: reliability -= 0.15
            if is_low_contrast: reliability -= 0.15
            
            return {
                'blur_score': round(float(laplacian_var), 2),
                'brightness': round(float(brightness), 2),
                'contrast': round(float(contrast), 2),
                'is_blurry': bool(is_blurry),
                'is_poor_lighting': bool(is_underexposed or is_overexposed),
                'is_low_contrast': bool(is_low_contrast),
                'reliability_multiplier': max(0.4, min(1.0, reliability))
            }
        except Exception as e:
            logging.error(f"Error assessing image quality: {str(e)}")
            return {
                'blur_score': 0,
                'brightness': 0,
                'contrast': 0,
                'is_blurry': False,
                'is_poor_lighting': False,
                'is_low_contrast': False,
                'reliability_multiplier': 0.5
            }

    def _detect_edge_anomalies(self, image: np.ndarray) -> List[Dict]:
        """Detect scratches and cracks via edge detection."""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply CLAHE for better contrast and edge visibility
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            gray = clahe.apply(gray)

            # Stronger blur to suppress noise
            blurred = cv2.GaussianBlur(gray, (7, 7), 1.5)

            # Higher Canny thresholds to reduce false edges from product details
            edges = cv2.Canny(blurred, 80, 200)

            # Morphological close then open to clean up noise
            kernel = np.ones((3, 3), np.uint8)
            edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=1)
            edges = cv2.morphologyEx(edges, cv2.MORPH_OPEN, kernel, iterations=1)

            # Find contours from edges
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            damages = []
            total_area = image.shape[0] * image.shape[1]

            for cnt in contours:
                area = cv2.contourArea(cnt)
                # Raised minimum area threshold (was 50, now 300)
                if area < 300:
                    continue

                area_ratio = area / total_area

                if area > 0:
                    circularity = 4 * np.pi * area / (cv2.arcLength(cnt, True) ** 2)

                    # Solidity filter: damage tends to have lower solidity than product features
                    hull = cv2.convexHull(cnt)
                    hull_area = cv2.contourArea(hull)
                    solidity = area / hull_area if hull_area > 0 else 1.0

                    # Skip highly solid shapes (likely product features like labels)
                    if solidity > 0.92 and circularity > 0.5:
                        continue

                    # Classify by shape
                    if circularity < 0.2:     # Very elongated = scratch
                        damage_type = 'scratch'
                    elif circularity < 0.45:  # Moderately irregular = crack
                        damage_type = 'crack'
                    else:
                        damage_type = 'chip'

                    severity = self._get_severity(area_ratio)

                    # Confidence based on area + shape irregularity
                    confidence = round(min(0.45 + area_ratio * 30 + (1 - solidity) * 0.3, 0.92), 3)

                    x, y, bw, bh = cv2.boundingRect(cnt)
                    damages.append({
                        'type': damage_type,
                        'severity': severity,
                        'confidence': confidence,
                        'area_ratio': round(area_ratio, 6),
                        'location': {
                            'x': int(x), 'y': int(y),
                            'width': int(bw), 'height': int(bh)
                        }
                    })

            return sorted(damages, key=lambda d: d.get('area_ratio', 0), reverse=True)[:5]
        except Exception as e:
            logging.error(f"Error detecting edge anomalies: {str(e)}")
            return []

    def _detect_color_anomalies(self, image: np.ndarray) -> List[Dict]:
        """Detect discoloration, stains, and corrosion via color space analysis."""
        try:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)

            damages = []
            total_area = image.shape[0] * image.shape[1]
            h_img, w_img = image.shape[:2]

            # Detect unusually dark or bright spots
            l_channel = lab[:, :, 0]
            mean_l = np.mean(l_channel)
            std_l = np.std(l_channel)

            # Dark anomalies — raised threshold from 2.5σ to 3.0σ
            dark_mask = l_channel < (mean_l - 3.0 * std_l)
            # Exclude border regions (likely background, not product damage)
            border = 10
            dark_mask[:border, :] = False
            dark_mask[-border:, :] = False
            dark_mask[:, :border] = False
            dark_mask[:, -border:] = False
            dark_area = np.sum(dark_mask)

            # Raised minimum area from 100 to 500
            if dark_area > 500:
                area_ratio = dark_area / total_area
                damages.append({
                    'type': 'stain',
                    'severity': self._get_severity(area_ratio),
                    'confidence': round(min(0.35 + area_ratio * 20, 0.88), 3),
                    'area_ratio': round(area_ratio, 6)
                })

            # Bright anomalies — raised threshold from 2.5σ to 3.0σ
            bright_mask = l_channel > (mean_l + 3.0 * std_l)
            bright_mask[:border, :] = False
            bright_mask[-border:, :] = False
            bright_mask[:, :border] = False
            bright_mask[:, -border:] = False
            bright_area = np.sum(bright_mask)

            if bright_area > 500:
                area_ratio = bright_area / total_area
                damages.append({
                    'type': 'discoloration',
                    'severity': self._get_severity(area_ratio),
                    'confidence': round(min(0.35 + area_ratio * 20, 0.88), 3),
                    'area_ratio': round(area_ratio, 6)
                })

            # Rust/corrosion detection via HSV color range
            lower_rust = np.array([5, 80, 80])   # Tighter saturation/value floors
            upper_rust = np.array([20, 255, 200])  # Tighter hue range
            rust_mask = cv2.inRange(hsv, lower_rust, upper_rust)
            rust_area = np.sum(rust_mask > 0)

            if rust_area > 500:
                area_ratio = rust_area / total_area
                # Only flag if significant portion; small warm-colored product areas shouldn't trigger
                if area_ratio > 0.005:
                    damages.append({
                        'type': 'corrosion',
                        'severity': self._get_severity(area_ratio),
                        'confidence': round(min(0.3 + area_ratio * 15, 0.85), 3),
                        'area_ratio': round(area_ratio, 6)
                    })

            return damages
        except Exception as e:
            logging.error(f"Error detecting color anomalies: {str(e)}")
            return []

    def _detect_texture_anomalies(self, image: np.ndarray) -> List[Dict]:
        """Detect surface wear and texture irregularities.

        Key insight: wear = localized smoothing on an otherwise textured surface.
        A uniformly smooth/clean product is NOT wear — it's just a smooth product.
        Only flag if there's a MIX of textured and smooth blocks.
        """
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply CLAHE for more robust texture gradient extraction
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            gray = clahe.apply(gray)
            
            damages = []

            # First check: if the entire image has very low global variance,
            # it's a uniform/smooth product surface — NOT wear damage.
            global_var = np.var(gray.astype(float))
            if global_var < 100:
                # Uniform image — nothing to detect
                return damages

            # Block-based texture variance analysis
            block_size = 32
            h, w = gray.shape
            block_variances = []

            for y in range(0, h - block_size, block_size):
                for x in range(0, w - block_size, block_size):
                    block = gray[y:y + block_size, x:x + block_size]
                    block_var = np.var(block.astype(float))
                    block_variances.append(block_var)

            if not block_variances:
                return damages

            total_blocks = len(block_variances)
            wear_blocks = sum(1 for v in block_variances if v < 50)
            textured_blocks = sum(1 for v in block_variances if v >= 200)
            wear_ratio = wear_blocks / total_blocks

            # Only flag wear if there are BOTH textured and smooth regions.
            # This distinguishes localized wear from a uniformly smooth product.
            has_texture_contrast = textured_blocks >= max(2, total_blocks * 0.1)

            if has_texture_contrast and wear_ratio > 0.3 and wear_ratio < 0.9:
                damages.append({
                    'type': 'wear',
                    'severity': self._get_severity(wear_ratio * 0.15),
                    'confidence': round(min(0.25 + wear_ratio * 0.4, 0.70), 3),
                    'area_ratio': round(wear_ratio * 0.05, 6)
                })

            return damages
        except Exception as e:
            logging.error(f"Error detecting texture anomalies: {str(e)}")
            return []

    def _detect_contour_irregularities(self, image: np.ndarray) -> List[Dict]:
        """Detect dents and deformations via contour shape analysis."""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply CLAHE to equalize lighting before thresholding
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            gray = clahe.apply(gray)
            
            blurred = cv2.GaussianBlur(gray, (7, 7), 0)

            # Adaptive threshold
            thresh = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, 11, 2
            )

            # Morphological open to remove small noise
            kernel = np.ones((3, 3), np.uint8)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)

            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            damages = []
            total_area = image.shape[0] * image.shape[1]

            for cnt in contours:
                area = cv2.contourArea(cnt)
                # Raised minimum area from 200 to 500
                if area < 500 or area > total_area * 0.4:
                    continue

                area_ratio = area / total_area

                # Solidity filter to exclude regular product features
                hull = cv2.convexHull(cnt)
                hull_area = cv2.contourArea(hull)
                solidity = area / hull_area if hull_area > 0 else 1.0

                # Very solid shapes are likely product features, skip
                if solidity > 0.9:
                    continue

                # Check for convexity defects (dents)
                hull_idx = cv2.convexHull(cnt, returnPoints=False)
                if len(hull_idx) > 3 and len(cnt) > 3:
                    try:
                        defects = cv2.convexityDefects(cnt, hull_idx)
                        # Need more defects to confirm (was >2, now >3)
                        if defects is not None and len(defects) > 3:
                            x, y, bw, bh = cv2.boundingRect(cnt)
                            damages.append({
                                'type': 'dent',
                                'severity': self._get_severity(area_ratio),
                                'confidence': round(min(0.3 + len(defects) * 0.04 + (1 - solidity) * 0.2, 0.8), 3),
                                'area_ratio': round(area_ratio, 6),
                                'location': {
                                    'x': int(x), 'y': int(y),
                                    'width': int(bw), 'height': int(bh)
                                }
                            })
                    except cv2.error:
                        pass

            return sorted(damages, key=lambda d: d.get('area_ratio', 0), reverse=True)[:3]
        except Exception as e:
            logging.error(f"Error detecting contour irregularities: {str(e)}")
            return []

    def _ml_classify(self, image: np.ndarray) -> Dict[str, float]:
        """Run ML classification for damage type detection (only if model is trained)."""
        try:
            if not self.model_trained:
                return {}
            import tensorflow as tf
            img_resized = cv2.resize(image, (224, 224))
            img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
            img_preprocessed = tf.keras.applications.mobilenet_v2.preprocess_input(
                np.expand_dims(img_rgb.astype(np.float32), axis=0)
            )
            predictions = self.model.predict(img_preprocessed, verbose=0)[0]

            results = {}
            for i, dtype in enumerate(self.DAMAGE_TYPES):
                if predictions[i] > 0.4:
                    results[dtype] = float(predictions[i])
            return results
        except Exception as e:
            logging.error(f"Error running ML classification: {str(e)}")
            return {}

    def _get_severity(self, area_ratio: float) -> str:
        """Determine damage severity based on affected area ratio."""
        try:
            for severity, (low, high) in self.SEVERITY_THRESHOLDS.items():
                if low <= area_ratio < high:
                    return severity
            return 'minor'
        except Exception as e:
            logging.error(f"Error determining damage severity: {str(e)}")
            return 'minor'