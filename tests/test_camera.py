#!/usr/bin/env python3

import cv2
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.camera.camera_controller import CameraController
from loguru import logger


def test_camera():
    logger.info("Testing camera...")
    
    camera = CameraController()
    if not camera.initialize():
        logger.error("Camera init failed")
        return False
    
    logger.info(f"Camera: {camera.get_camera_info()}")
    
    frame_count = 0
    start_time = time.time()
    
    try:
        while frame_count < 100:
            frame = camera.capture_frame()
            if frame is None:
                continue
            
            frame_count += 1
            cv2.imshow('Camera Test', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
            time.sleep(0.033)
        
        elapsed = time.time() - start_time
        fps = frame_count / elapsed
        logger.info(f"{frame_count} frames, {elapsed:.1f}s, {fps:.1f} FPS")
        
    except KeyboardInterrupt:
        logger.info("Interrupted")
    finally:
        camera.release()
        cv2.destroyAllWindows()
    
    return True


if __name__ == "__main__":
    test_camera()

