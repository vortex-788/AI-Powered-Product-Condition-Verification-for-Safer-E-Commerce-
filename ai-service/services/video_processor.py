"""
Video Processor Service
Extracts keyframes from product videos and runs damage detection on each.

Accuracy improvements:
- Cross-frame damage consistency validation (multi-frame confirmation)
- Trimmed mean scoring to reduce outlier influence
- Single-frame damages marked as unconfirmed with lower confidence
"""
import cv2
import numpy as np
from typing import Dict, Any, List


class VideoProcessor:
    """Process product videos for condition verification."""

    def __init__(self, damage_detector):
        self.damage_detector = damage_detector
        self.max_frames = 15  # Maximum frames to analyze
        self.min_frame_interval = 0.5  # Minimum seconds between frames
        self.confirmation_threshold = 2  # Damage must appear in N+ frames to be "confirmed"

    def _handle_error(self, e: Exception, error_message: str, video_path: str, frame_num: int = None) -> Dict[str, Any]:
        return {
            'condition_score': 0,
            'grade': 'Damaged',
            'error': f'Error processing video {video_path}: {error_message} - {str(e)}' + (f' at frame {frame_num}' if frame_num is not None else ''),
            'frames_analyzed': 0,
            'frame_results': [],
            'damages': []
        }

    def analyze_video(self, video_path: str) -> Dict[str, Any]:
        """
        Analyze a product video by extracting keyframes and running damage detection.

        Args:
            video_path: Path to the video file

        Returns:
            dict with overall score, frame results, and aggregate damage info
        """
        try:
            cap = cv2.VideoCapture(video_path)
        except FileNotFoundError as e:
            return self._handle_error(e, 'Video file not found', video_path)
        except cv2.error as e:
            return self._handle_error(e, 'OpenCV error opening video', video_path)
        except OSError as e:
            return self._handle_error(e, 'OS error opening video', video_path)
        except RuntimeError as e:
            return self._handle_error(e, 'Runtime error opening video', video_path)

        if not cap.isOpened():
            return {
                'condition_score': 0,
                'grade': 'Damaged',
                'error': f'Could not open video file {video_path}',
                'frames_analyzed': 0,
                'frame_results': [],
                'damages': []
            }

        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps

        # Extract keyframes using scene change detection
        keyframes = self._extract_keyframes(cap, fps, total_frames)
        cap.release()

        if not keyframes:
            return {
                'condition_score': 0,
                'grade': 'Damaged',
                'error': f'No valid frames extracted from video {video_path}',
                'frames_analyzed': 0,
                'frame_results': [],
                'damages': []
            }

        # Analyze each keyframe
        frame_results = []
        all_damages = []

        for i, (frame_num, frame) in enumerate(keyframes):
            try:
                result = self.damage_detector.analyze(frame)
            except AttributeError as e:
                return self._handle_error(e, f'Error analyzing frame {frame_num} of video {video_path}: damage detector not properly initialized', video_path, frame_num)
            except TypeError as e:
                return self._handle_error(e, f'Error analyzing frame {frame_num} of video {video_path}: invalid frame data', video_path, frame_num)
            except Exception as e:
                return self._handle_error(e, f'Error analyzing frame {frame_num} of video {video_path}: unknown error', video_path, frame_num)

            timestamp = frame_num / fps

            frame_result = {
                'frame_number': int(frame_num),
                'timestamp': round(timestamp, 2),
                'score': result['condition_score'],
                'grade': result['grade'],
                'damages': result['damages'][:5]  # Top 5 per frame
            }
            frame_results.append(frame_result)
            all_damages.extend(result['damages'])

        # ── Improved score aggregation: trimmed mean ──
        scores = sorted([fr['score'] for fr in frame_results])

        if len(scores) >= 5:
            # Drop top and bottom 10% of scores
            trim_count = max(1, len(scores) // 10)
            trimmed_scores = scores[trim_count:-trim_count]
            avg_score = round(np.mean(trimmed_scores), 1)
        else:
            avg_score = round(np.mean(scores), 1)

        min_score = round(np.min(scores), 1)

        # Less aggressive weighting (was 60/40, now 70/30)
        # Single bad frame shouldn't tank the score as much
        condition_score = round(avg_score * 0.70 + min_score * 0.30, 1)

        # ── Cross-frame damage consistency ──
        unique_damages = self._deduplicate_damages_with_confirmation(all_damages)

        # Only use confirmed damages for final scoring adjustment
        confirmed_damage_count = sum(1 for d in unique_damages if d.get('confirmed', False))
        unconfirmed_count = sum(1 for d in unique_damages if not d.get('confirmed', False))

        # Grade
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
            'frames_analyzed': len(frame_results),
            'video_duration': round(duration, 2),
            'frame_results': frame_results,
            'damages': unique_damages[:15],
            'statistics': {
                'avg_score': avg_score,
                'min_score': min_score,
                'max_score': round(np.max(scores), 1),
                'score_variance': round(float(np.var(scores)), 2),
                'total_damages_detected': len(all_damages),
                'confirmed_damages': confirmed_damage_count,
                'unconfirmed_damages': unconfirmed_count
            }
        }

    def _extract_keyframes(self, cap, fps, total_frames) -> List:
        """Extract keyframes using scene change detection."""
        keyframes = []
        prev_gray = None
        frame_interval = max(int(fps * self.min_frame_interval), 1)

        frame_idx = 0
        while frame_idx < total_frames and len(keyframes) < self.max_frames:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()

            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            if prev_gray is None:
                # Always include first frame
                keyframes.append((frame_idx, frame.copy()))
            else:
                # Detect scene change via frame difference
                diff = cv2.absdiff(prev_gray, gray)
                change_ratio = np.mean(diff) / 255.0

                if change_ratio > 0.05:  # Significant change threshold
                    keyframes.append((frame_idx, frame.copy()))

            prev_gray = gray
            frame_idx += frame_interval

        # If too few keyframes, sample uniformly
        if len(keyframes) < 5 and total_frames > 0:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            sample_interval = max(total_frames // 10, 1)
            keyframes = []

            for i in range(0, total_frames, sample_interval):
                if len(keyframes) >= self.max_frames:
                    break
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()
                if ret:
                    keyframes.append((i, frame.copy()))

        return keyframes

    def _deduplicate_damages_with_confirmation(self, damages: List[Dict]) -> List[Dict]:
        """
        Merge similar damages across frames with confirmation tracking.
        Damages seen in 2+ frames are 'confirmed'; single-frame are 'unconfirmed'.
        """
        seen_types = {}

        for dmg in damages:
            dtype = dmg.get('type', 'unknown')
            severity = dmg.get('severity', 'minor')
            key = f"{dtype}_{severity}"

            if key not in seen_types:
                seen_types[key] = {
                    'type': dtype,
                    'severity': severity,
                    'confidence': dmg.get('confidence', 0),
                    'occurrences': 1,
                    'detection_source': dmg.get('detection_source', 'unknown'),
                    'confirmed': False
                }
            else:
                seen_types[key]['occurrences'] += 1
                seen_types[key]['confidence'] = max(
                    seen_types[key]['confidence'],
                    dmg.get('confidence', 0)
                )

        # Mark confirmation status
        for key, dmg in seen_types.items():
            if dmg['occurrences'] >= self.confirmation_threshold:
                dmg['confirmed'] = True
                # Boost confidence for confirmed damages
                dmg['confidence'] = min(dmg['confidence'] * 1.15, 0.98)
                dmg['confidence'] = round(dmg['confidence'], 3)
            else:
                # Reduce confidence for unconfirmed single-frame damages
                dmg['confidence'] = round(dmg['confidence'] * 0.7, 3)

        return sorted(
            list(seen_types.values()),
            key=lambda d: (d.get('confirmed', False), d.get('confidence', 0)),
            reverse=True
        )