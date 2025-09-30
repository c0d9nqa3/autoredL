#!/usr/bin/env python3
"""
Detection testing script for AutoRedL
"""

import cv2
import time
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.camera.camera_controller import CameraController
from src.detection.human_detector import HumanDetector, FallbackDetector, ONNX_AVAILABLE
from loguru import logger


def test_detection():
    """Test human detection"""
    logger.info("Testing human detection...")
    
    # Initialize camera
    camera = CameraController(camera_id=0, resolution=(640, 480), fps=30)
    
    if not camera.initialize():
        logger.error("Camera initialization failed")
        return False
    
    # Initialize detector
    model_path = "models/yolov5s.onnx"
    
    if ONNX_AVAILABLE and Path(model_path).exists():
        detector = HumanDetector(
            model_path=model_path,
            confidence_threshold=0.5,
            nms_threshold=0.4,
            input_size=(640, 640)
        )
        
        if not detector.initialize():
            logger.warning("ONNX detector failed, using HOG fallback")
            detector = FallbackDetector()
    else:
        logger.info("Using HOG fallback detector")
        detector = FallbackDetector()
    
    logger.info("Detection system initialized")
    
    frame_count = 0
    detection_count = 0
    start_time = time.time()
    
    try:
        while True:
            # Capture frame
            frame = camera.capture_frame()
            if frame is None:
                continue
            
            frame_count += 1
            
            # Detect humans
            detections = detector.detect_humans(frame)
            
            if detections:
                detection_count += len(detections)
                logger.info(f"Found {len(detections)} human(s)")
                
                # Get largest detection
                largest = detector.get_largest_detection(detections)
                if largest:
                    center_x, center_y = largest.center
                    logger.info(f"Largest detection center: ({center_x:.1f}, {center_y:.1f}), confidence: {largest.confidence:.2f}")
            
            # Draw detections
            display_frame = detector.draw_detections(frame, detections)
            
            # Add frame info
            cv2.putText(display_frame, f"Frame: {frame_count}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(display_frame, f"Detections: {len(detections)}", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Display frame
            cv2.imshow('Detection Test', display_frame)
            
            # Exit on 'q' key
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        elapsed_time = time.time() - start_time
        avg_fps = frame_count / elapsed_time
        logger.info(f"Processed {frame_count} frames in {elapsed_time:.1f}s (avg {avg_fps:.1f} FPS)")
        logger.info(f"Total detections: {detection_count}")
        
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    
    finally:
        camera.release()
        cv2.destroyAllWindows()
    
    return True


if __name__ == "__main__":
    test_detection()

