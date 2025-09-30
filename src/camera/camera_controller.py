import cv2
import numpy as np
from loguru import logger


class CameraController:
    def __init__(self, camera_id=0, resolution=(640, 480), fps=30):
        self.camera_id = camera_id
        self.resolution = resolution
        self.fps = fps
        self.cap = None
        self.is_initialized = False
        
    def initialize(self):
        try:
            backends = [cv2.CAP_V4L2, cv2.CAP_GSTREAMER, cv2.CAP_ANY]
            
            for backend in backends:
                self.cap = cv2.VideoCapture(self.camera_id, backend)
                if self.cap.isOpened():
                    break
            else:
                return False
            
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            
            self.is_initialized = True
            return True
        except Exception:
            return False
    
    def capture_frame(self):
        if not self.is_initialized or not self.cap:
            return None
        
        ret, frame = self.cap.read()
        return frame if ret else None
    
    def get_camera_info(self):
        if not self.is_initialized or not self.cap:
            return {}
        
        return {
            'width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': self.cap.get(cv2.CAP_PROP_FPS),
        }
    
    def set_property(self, prop_id, value):
        if self.is_initialized and self.cap:
            return self.cap.set(prop_id, value)
        return False
    
    def release(self):
        if self.cap:
            self.cap.release()
            self.is_initialized = False

