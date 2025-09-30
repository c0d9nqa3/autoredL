import numpy as np
from loguru import logger
import time

from ..detection.human_detector import BoundingBox


class TargetTracker:
    def __init__(self, frame_width=640, frame_height=480):
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.frame_center_x = frame_width // 2
        self.frame_center_y = frame_height // 2
        
        self.current_target = None
        self.target_lost_time = 0.0
        self.max_lost_time = 2.0
        
        self.position_history = []
        self.history_size = 5
        self.deadzone_x = 20
        self.deadzone_y = 20
    
    def update_target(self, detections):
        current_time = time.time()
        
        if not detections:
            if self.current_target:
                if self.target_lost_time == 0:
                    self.target_lost_time = current_time
                elif current_time - self.target_lost_time > self.max_lost_time:
                    self.current_target = None
                    self.target_lost_time = 0
                    self.position_history.clear()
            return self.current_target
        
        self.target_lost_time = 0
        
        if not self.current_target:
            self.current_target = max(detections, key=lambda det: det.area)
        else:
            current_center = self.current_target.center
            self.current_target = min(detections, 
                                    key=lambda det: self.distance(det.center, current_center))
        
        self.add_to_history(self.current_target.center)
        return self.current_target
    
    def get_servo_angles(self, target=None, max_pan=90, max_tilt=45):
        if not target:
            target = self.current_target
        
        if not target:
            return 0.0, 0.0
        
        target_x, target_y = self.get_smoothed_position()
        error_x = target_x - self.frame_center_x
        error_y = target_y - self.frame_center_y
        
        if abs(error_x) < self.deadzone_x:
            error_x = 0
        if abs(error_y) < self.deadzone_y:
            error_y = 0
        
        norm_x = error_x / (self.frame_width / 2)
        norm_y = error_y / (self.frame_height / 2)
        
        pan_angle = max(-max_pan, min(max_pan, norm_x * max_pan))
        tilt_angle = max(-max_tilt, min(max_tilt, norm_y * max_tilt))
        
        return pan_angle, tilt_angle
    
    def get_tracking_error(self):
        if not self.current_target:
            return 0.0, 0.0
        
        target_x, target_y = self.get_smoothed_position()
        return target_x - self.frame_center_x, target_y - self.frame_center_y
    
    def is_target_centered(self, threshold=30.0):
        if not self.current_target:
            return False
        
        error_x, error_y = self.get_tracking_error()
        return np.sqrt(error_x**2 + error_y**2) < threshold
    
    def has_target(self):
        return self.current_target is not None
    
    def reset(self):
        self.current_target = None
        self.target_lost_time = 0.0
        self.position_history.clear()
    
    def set_frame_size(self, width, height):
        self.frame_width = width
        self.frame_height = height
        self.frame_center_x = width // 2
        self.frame_center_y = height // 2
    
    def set_deadzone(self, deadzone_x, deadzone_y):
        self.deadzone_x = deadzone_x
        self.deadzone_y = deadzone_y
    
    def distance(self, pos1, pos2):
        return np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
    
    def add_to_history(self, position):
        self.position_history.append(position)
        if len(self.position_history) > self.history_size:
            self.position_history.pop(0)
    
    def get_smoothed_position(self):
        if not self.position_history:
            return self.frame_center_x, self.frame_center_y
        
        if len(self.position_history) == 1:
            return self.position_history[0]
        
        x_sum = sum(pos[0] for pos in self.position_history)
        y_sum = sum(pos[1] for pos in self.position_history)
        return x_sum / len(self.position_history), y_sum / len(self.position_history)
    
    def get_target_info(self):
        if not self.current_target:
            return {'has_target': False}
        
        error_x, error_y = self.get_tracking_error()
        pan_angle, tilt_angle = self.get_servo_angles()
        
        return {
            'has_target': True,
            'target': self.current_target.to_dict(),
            'error': {'x': error_x, 'y': error_y},
            'servo_angles': {'pan': pan_angle, 'tilt': tilt_angle},
            'centered': self.is_target_centered(),
            'smoothed_position': self.get_smoothed_position()
        }

