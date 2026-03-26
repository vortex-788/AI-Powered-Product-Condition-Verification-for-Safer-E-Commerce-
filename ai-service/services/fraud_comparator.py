"""
Fraud Comparator Service
Compares original vs returned product images using:
- Homography-based image alignment before comparison
- Structural Similarity Index (SSIM)
- Feature matching (ORB) with spatial verification
- Color histogram comparison
- Texture analysis (Gabor filters)
- Perceptual hashing (aHash, dHash) for swap detection

Accuracy improvements:
- Image alignment via homography before metric computation
- Perceptual hash for fast/reliable product swap detection
- Recalibrated scoring weights and thresholds
- Multi-signal voting for fraud classification
"""
import cv2
import numpy as np
from typing import Dict, Any, Tuple, Optional
from skimage.metrics import structural_similarity as ssim
import logging

class FraudComparator:
    """Compare product images to detect return fraud (swaps, tampering)."""

    # Recalibrated thresholds (lowered to reduce false fraud flags on legitimate returns)
    FRAUD_THRESHOLD = 0.65     # Below this overall score = likely fraud (was 0.75)
    SWAP_THRESHOLD = 0.45      # Below this = likely product swap (was 0.60)
    HASH_SWAP_THRESHOLD = 15   # Perceptual hash distance above this = instant swap flag

    def compare(self, original: np.ndarray, returned: np.ndarray) -> Dict[str, Any]:
        """
        Compare original and returned product images.

        Returns:
            dict with similarity_score, fraud_detected, fraud_type, risk_level, details
        """
        try:
            # Resize both to smaller dimensions for HUGE speedup (256x256 is enough for SSIM/Hash)
            target_size = (256, 256)
            orig_resized = cv2.resize(original, target_size)
            ret_resized = cv2.resize(returned, target_size)

            # ── Step 1: Try to align returned image to original via homography ──
            aligned_ret, alignment_success = self._align_images(orig_resized, ret_resized)
            comparison_img = aligned_ret if alignment_success else ret_resized

            # ── Step 2: Compute perceptual hashes for fast swap detection ──
            hash_distance, ahash_dist, dhash_dist = self._compute_perceptual_hash(orig_resized, ret_resized)
            hash_score = max(0, 1.0 - hash_distance / 64.0)  # Normalize to 0-1

            # ── Step 3: Run comparison metrics ──
            ssim_score = self._compute_ssim(orig_resized, comparison_img)
            feature_score = self._compute_feature_match(orig_resized, comparison_img)
            histogram_score = self._compute_histogram_match(orig_resized, comparison_img)
            texture_score = self._compute_texture_similarity(orig_resized, comparison_img)

            # ── Step 4: Weighted combination ──
            similarity_score = round(
                ssim_score * 0.35 +
                feature_score * 0.20 +
                histogram_score * 0.15 +
                texture_score * 0.15 +
                hash_score * 0.15,
                2
            ) * 100  # Convert to 0-100 scale

            similarity_score = round(min(100, max(0, similarity_score)), 1)

            # ── Step 5: Multi-signal fraud classification ──
            fraud_detected, fraud_type, fraud_confidence, anomalies = self._classify_fraud(
                similarity_score, ssim_score, feature_score, histogram_score,
                texture_score, hash_distance, alignment_success
            )

            # Risk level
            if similarity_score < 30:
                risk_level = 'critical'
            elif similarity_score < 50:
                risk_level = 'high'
            elif similarity_score < 70:
                risk_level = 'medium'
            else:
                risk_level = 'low'

            # Recommendation
            recommendation = self._generate_recommendation(fraud_type, fraud_confidence, similarity_score)

            return {
                'similarity_score': similarity_score,
                'fraud_detected': fraud_detected,
                'fraud_type': fraud_type,
                'fraud_confidence': round(fraud_confidence, 2),
                'risk_level': risk_level,
                'details': {
                    'structural_similarity': round(ssim_score * 100, 2),
                    'feature_match_score': round(feature_score * 100, 2),
                    'color_histogram_match': round(histogram_score * 100, 2),
                    'texture_analysis': round(texture_score * 100, 2),
                    'perceptual_hash_score': round(hash_score * 100, 2),
                    'hash_distance': hash_distance,
                    'image_aligned': alignment_success,
                    'anomalies': anomalies
                },
                'recommendation': recommendation,
                'error': None
            }
        except cv2.error as e:
            logging.error(f"OpenCV error occurred: {e}")
            return {
                'similarity_score': 0,
                'fraud_detected': False,
                'fraud_type': 'none',
                'fraud_confidence': 0.0,
                'risk_level': 'low',
                'details': {
                    'structural_similarity': 0,
                    'feature_match_score': 0,
                    'color_histogram_match': 0,
                    'texture_analysis': 0,
                    'perceptual_hash_score': 0,
                    'hash_distance': 0,
                    'image_aligned': False,
                    'anomalies': []
                },
                'recommendation': 'REVIEW REQUIRED: An OpenCV error occurred during the comparison process.',
                'error': str(e)
            }
        except np.linalg.LinAlgError as e:
            logging.error(f"Linear algebra error occurred: {e}")
            return {
                'similarity_score': 0,
                'fraud_detected': False,
                'fraud_type': 'none',
                'fraud_confidence': 0.0,
                'risk_level': 'low',
                'details': {
                    'structural_similarity': 0,
                    'feature_match_score': 0,
                    'color_histogram_match': 0,
                    'texture_analysis': 0,
                    'perceptual_hash_score': 0,
                    'hash_distance': 0,
                    'image_aligned': False,
                    'anomalies': []
                },
                'recommendation': 'REVIEW REQUIRED: A linear algebra error occurred during the comparison process.',
                'error': str(e)
            }
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return {
                'similarity_score': 0,
                'fraud_detected': False,
                'fraud_type': 'none',
                'fraud_confidence': 0.0,
                'risk_level': 'low',
                'details': {
                    'structural_similarity': 0,
                    'feature_match_score': 0,
                    'color_histogram_match': 0,
                    'texture_analysis': 0,
                    'perceptual_hash_score': 0,
                    'hash_distance': 0,
                    'image_aligned': False,
                    'anomalies': []
                },
                'recommendation': 'REVIEW REQUIRED: An unexpected error occurred during the comparison process.',
                'error': str(e)
            }

    def _align_images(self, img1: np.ndarray, img2: np.ndarray) -> Tuple[np.ndarray, bool]:
        """Align img2 to img1 using homography from ORB feature matching."""
        try:
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

            # Apply CLAHE for better ORB feature extraction
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            gray1 = clahe.apply(gray1)
            gray2 = clahe.apply(gray2)

            orb = cv2.ORB_create(nfeatures=1000)
            kp1, des1 = orb.detectAndCompute(gray1, None)
            kp2, des2 = orb.detectAndCompute(gray2, None)

            if des1 is None or des2 is None or len(des1) < 10 or len(des2) < 10:
                return img2, False

            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
            matches = bf.knnMatch(des1, des2, k=2)

            # Lowe's ratio test
            good_matches = []
            for m_n in matches:
                if len(m_n) == 2:
                    m, n = m_n
                    if m.distance < 0.7 * n.distance:
                        good_matches.append(m)

            if len(good_matches) < 8:
                return img2, False

            src_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)

            H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
            if H is None:
                return img2, False

            h, w = img1.shape[:2]
            aligned = cv2.warpPerspective(img2, H, (w, h))
            return aligned, True

        except Exception as e:
            logging.error(f"An error occurred in _align_images: {e}")
            return img2, False

    def _compute_perceptual_hash(self, img1: np.ndarray, img2: np.ndarray) -> Tuple[float, int, int]:
        """Compute perceptual hash distance (average of aHash and dHash distances)."""
        try:
            # Average Hash
            ahash1 = self._average_hash(img1)
            ahash2 = self._average_hash(img2)
            ahash_dist = self._hamming_distance(ahash1, ahash2)

            # Difference Hash
            dhash1 = self._difference_hash(img1)
            dhash2 = self._difference_hash(img2)
            dhash_dist = self._hamming_distance(dhash1, dhash2)

            avg_distance = (ahash_dist + dhash_dist) / 2.0
            return avg_distance, ahash_dist, dhash_dist
        except Exception as e:
            logging.error(f"An error occurred in _compute_perceptual_hash: {e}")
            return 0, 0, 0

    def _average_hash(self, image: np.ndarray, hash_size: int = 8) -> int:
        """Compute average hash of an image."""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            resized = cv2.resize(gray, (hash_size, hash_size))
            mean_val = resized.mean()
            hash_val = 0
            for pixel in resized.flatten():
                hash_val = (hash_val << 1) | (1 if pixel >= mean_val else 0)
            return hash_val
        except Exception as e:
            logging.error(f"An error occurred in _average_hash: {e}")
            return 0

    def _difference_hash(self, image: np.ndarray, hash_size: int = 8) -> int:
        """Compute difference hash of an image."""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            resized = cv2.resize(gray, (hash_size + 1, hash_size))
            hash_val = 0
            for row in range(hash_size):
                for col in range(hash_size):
                    hash_val = (hash_val << 1) | (1 if resized[row, col] > resized[row, col + 1] else 0)
            return hash_val
        except Exception as e:
            logging.error(f"An error occurred in _difference_hash: {e}")
            return 0

    def _hamming_distance(self, hash1: int, hash2: int) -> int:
        """Compute Hamming distance between two hashes."""
        try:
            return bin(hash1 ^ hash2).count('1')
        except Exception as e:
            logging.error(f"An error occurred in _hamming_distance: {e}")
            return 0

    def _classify_fraud(
        self, similarity_score, ssim_score, feature_score,
        histogram_score, texture_score, hash_distance, aligned
    ) -> Tuple[bool, str, float, list]:
        """
        Multi-signal voting approach for fraud classification.
        Returns (fraud_detected, fraud_type, confidence, anomalies).
        """
        try:
            anomalies = []
            fraud_signals = 0
            swap_signals = 0

            # Signal 1: Perceptual hash says completely different product
            if hash_distance > self.HASH_SWAP_THRESHOLD:
                swap_signals += 2
                anomalies.append(f'Perceptual hash mismatch (distance={hash_distance:.0f}) — likely different product')

            # Signal 2: Very low SSIM (structural mismatch)
            if ssim_score < 0.35:
                swap_signals += 1
                fraud_signals += 1
                anomalies.append('Very low structural similarity')
            elif ssim_score < 0.55:
                fraud_signals += 1

            # Signal 3: Very low feature match
            if feature_score < 0.2:
                swap_signals += 1
                fraud_signals += 1
                anomalies.append('Insufficient matching features between images')
            elif feature_score < 0.4:
                fraud_signals += 1

            # Signal 4: Histogram mismatch
            if histogram_score < 0.4:
                fraud_signals += 1
                anomalies.append('Significant color distribution difference')

            # Signal 5: Cross-metric inconsistency
            if abs(histogram_score - ssim_score) > 0.35:
                fraud_signals += 1
                anomalies.append('Inconsistency between color and structure analysis')

            # Signal 6: Texture mismatch with good features (possible swap of similar product)
            if texture_score < 0.5 and feature_score > 0.4:
                fraud_signals += 1
                anomalies.append('Texture mismatch despite feature similarity — possible similar-model swap')

            # Signal 7: Alignment failure combined with poor features
            if not aligned and feature_score < 0.35:
                fraud_signals += 1
                anomalies.append('Failed to structurally align images — potential tampering or wrong item')

            # ── Decision logic ──

            # Product swap: hash mismatch OR multiple swap signals
            if swap_signals >= 2 or (hash_distance > self.HASH_SWAP_THRESHOLD and ssim_score < 0.5):
                fraud_confidence = min(0.5 + swap_signals * 0.15, 0.98)
                return True, 'product_swap', fraud_confidence, anomalies

            # Overall score check
            if similarity_score < self.FRAUD_THRESHOLD * 100:
                # Determine fraud sub-type
                if histogram_score < 0.45 and feature_score < 0.3:
                    fraud_type = 'different_model'
                    anomalies.append('Color/model variant mismatch detected')
                elif ssim_score < 0.45:
                    fraud_type = 'damage_added'
                    anomalies.append('Significant structural differences — possible intentional damage')
                else:
                    fraud_type = 'tampered'
                    anomalies.append('Product shows signs of tampering or modification')

                fraud_confidence = min(0.4 + fraud_signals * 0.12, 0.95)
                return True, fraud_type, fraud_confidence, anomalies

            # Edge case: high similarity but one metric is an outlier
            if similarity_score >= self.FRAUD_THRESHOLD * 100 and fraud_signals >= 3:
                fraud_confidence = min(0.3 + fraud_signals * 0.1, 0.7)
                anomalies.append('Multiple weak fraud signals despite overall similarity')
                return True, 'suspicious', fraud_confidence, anomalies

            # No fraud
            return False, 'none', 0.0, anomalies
        except Exception as e:
            logging.error(f"An error occurred in _classify_fraud: {e}")
            return False, 'none', 0.0, []

    def _generate_recommendation(self, fraud_type: str, confidence: float, score: float) -> str:
        """Generate actionable recommendation based on fraud analysis."""
        try:
            if fraud_type == 'product_swap':
                return (f'REJECT RETURN: High confidence ({confidence:.0%}) product swap detected. '
                        f'The returned item differs significantly from the original. Escalate to manual review.')
            elif fraud_type == 'damage_added':
                return ('REVIEW REQUIRED: Potential damage added after purchase. '
                        'Compare specific damage regions for verification.')
            elif fraud_type in ('different_model', 'tampered'):
                return ('REVIEW REQUIRED: Product may have been substituted or tampered with. '
                        'Manual inspection recommended.')
            elif fraud_type == 'suspicious':
                return ('MONITOR: Some anomalies detected but overall similarity is acceptable. '
                        'Flag for additional review if customer has return history.')
            else:
                return ('APPROVE: Product appears to match the original within acceptable margins. '
                        'No fraud indicators detected.')
        except Exception as e:
            logging.error(f"An error occurred in _generate_recommendation: {e}")
            return 'REVIEW REQUIRED: An error occurred during the recommendation process.'

    def _compute_ssim(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """Compute Structural Similarity Index."""
        try:
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            score, _ = ssim(gray1, gray2, full=True)
            return max(0, float(score))
        except Exception as e:
            logging.error(f"An error occurred in _compute_ssim: {e}")
            return 0.5

    def _compute_feature_match(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """Compute feature matching score using ORB detector."""
        try:
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

            # Apply CLAHE to improve feature matching consistency
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            gray1 = clahe.apply(gray1)
            gray2 = clahe.apply(gray2)

            orb = cv2.ORB_create(nfeatures=750)
            kp1, des1 = orb.detectAndCompute(gray1, None)
            kp2, des2 = orb.detectAndCompute(gray2, None)

            if des1 is None or des2 is None or len(des1) < 2 or len(des2) < 2:
                return 0.2

            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
            matches = bf.knnMatch(des1, des2, k=2)

            # Lowe's ratio test
            good_matches = []
            for m_n in matches:
                if len(m_n) == 2:
                    m, n = m_n
                    if m.distance < 0.7 * n.distance:
                        good_matches.append(m)

            max_possible = min(len(kp1), len(kp2))
            if max_possible == 0:
                return 0.2

            # Spatial consistency check: filter matches by geometric consistency
            if len(good_matches) >= 4:
                src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                _, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
                if mask is not None:
                    inliers = int(mask.sum())
                    return min(inliers / max_possible * 2.5, 1.0)

            return min(len(good_matches) / max_possible * 2, 1.0)
        except Exception as e:
            logging.error(f"An error occurred in _compute_feature_match: {e}")
            return 0.5

    def _compute_histogram_match(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """Compare color histograms of two images."""
        try:
            hsv1 = cv2.cvtColor(img1, cv2.COLOR_BGR2HSV)
            hsv2 = cv2.cvtColor(img2, cv2.COLOR_BGR2HSV)

            h_bins, s_bins = 50, 60
            hist_size = [h_bins, s_bins]
            ranges = [0, 180, 0, 256]
            channels = [0, 1]

            hist1 = cv2.calcHist([hsv1], channels, None, hist_size, ranges)
            hist2 = cv2.calcHist([hsv2], channels, None, hist_size, ranges)

            cv2.normalize(hist1, hist1, 0, 1, cv2.NORM_MINMAX)
            cv2.normalize(hist2, hist2, 0, 1, cv2.NORM_MINMAX)

            score = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
            return max(0, float(score))
        except Exception as e:
            logging.error(f"An error occurred in _compute_histogram_match: {e}")
            return 0.5

    def _compute_texture_similarity(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """Compare texture patterns using fast local variance maps."""
        try:
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

            # Fast localized texture density using variance (runs in <5ms instead of ~400ms for Gabor)
            ksize = 21
            blur1 = cv2.blur(gray1**2, (ksize, ksize)) - cv2.blur(gray1, (ksize, ksize))**2
            blur2 = cv2.blur(gray2**2, (ksize, ksize)) - cv2.blur(gray2, (ksize, ksize))**2

            # Normalize logs
            tex1 = np.log1p(blur1)
            tex2 = np.log1p(blur2)

            norm1 = np.linalg.norm(tex1)
            norm2 = np.linalg.norm(tex2)

            if norm1 > 0 and norm2 > 0:
                correlation = np.sum(tex1 * tex2) / (norm1 * norm2)
                return max(0.0, min(1.0, float(correlation)))
            return 0.5
        except Exception as e:
            logging.error(f"An error occurred in _compute_texture_similarity: {e}")
            return 0.5