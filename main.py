#!/usr/bin/env python3

import cv2
import yaml
import time
import signal
import sys
from pathlib import Path
from loguru import logger

from src.camera.camera_controller import CameraController
from src.servo.servo_controller import ServoController
from src.detection.human_detector import HumanDetector, FallbackDetector, ONNX_AVAILABLE
from src.laser.laser_controller import LaserController
from src.tracking.target_tracker import TargetTracker
from src.serial.serial_interface import SerialInterface, SerialDebugger


class AutoRedLSystem:
    def __init__(self, config_path="config/settings.yaml"):
        self.config = self.load_config(config_path)
        
        self.camera = None
        self.servo = None
        self.detector = None
        self.laser = None
        self.tracker = None
        self.serial = None
        self.debugger = None
        
        self.running = False
        self.initialized = False
        self.frame_count = 0
        self.start_time = time.time()
        
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
    
    def load_config(self, path):
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Config load failed: {e}")
            return {}
    
    def initialize(self):
        logger.info("Starting system...")
        
        # Camera setup
        cam_cfg = self.config.get('camera', {})
        self.camera = CameraController(
            camera_id=0,
            resolution=tuple(cam_cfg.get('resolution', [640, 480])),
            fps=cam_cfg.get('fps', 30)
        )
        if not self.camera.initialize():
            logger.error("Camera failed")
            return False
        
        # Servo setup
        servo_cfg = self.config.get('servo', {})
        self.servo = ServoController(
            pan_pin=servo_cfg.get('pan_pin', 18),
            tilt_pin=servo_cfg.get('tilt_pin', 19),
            frequency=servo_cfg.get('frequency', 50)
        )
        if not self.servo.initialize():
            logger.error("Servo failed")
            return False
        
        self.servo.set_limits(
            servo_cfg.get('pan_min', -90), servo_cfg.get('pan_max', 90),
            servo_cfg.get('tilt_min', -45), servo_cfg.get('tilt_max', 45)
        )
        
        # Detection setup
        det_cfg = self.config.get('detection', {})
        if ONNX_AVAILABLE and Path(det_cfg.get('model_path', '')).exists():
            self.detector = HumanDetector(
                model_path=det_cfg.get('model_path', 'models/yolov5s.onnx'),
                confidence_threshold=det_cfg.get('confidence_threshold', 0.5),
                nms_threshold=det_cfg.get('nms_threshold', 0.4),
                input_size=tuple(det_cfg.get('input_size', [640, 640]))
            )
            if not self.detector.initialize():
                self.detector = FallbackDetector()
        else:
            self.detector = FallbackDetector()
        
        # Laser setup
        laser_cfg = self.config.get('laser', {})
        self.laser = LaserController(
            enable_pin=laser_cfg.get('enable_pin', 20),
            safety_timeout=laser_cfg.get('safety_timeout', 5.0)
        )
        if not self.laser.initialize():
            logger.error("Laser failed")
            return False
        
        # Tracker setup
        res = cam_cfg.get('resolution', [640, 480])
        self.tracker = TargetTracker(frame_width=res[0], frame_height=res[1])
        
        # Serial setup (optional)
        serial_cfg = self.config.get('serial', {})
        if serial_cfg.get('enabled', False):
            self.serial = SerialInterface(
                port=serial_cfg.get('port', '/dev/ttyUSB0'),
                baudrate=serial_cfg.get('baudrate', 115200)
            )
            if self.serial.connect():
                self.debugger = SerialDebugger(self.serial)
                self.debugger.set_system_components(
                    camera=self.camera, servo=self.servo, laser=self.laser,
                    detector=self.detector, tracker=self.tracker
                )
        
        self.servo.center_servos()
        self.initialized = True
        logger.info("System ready")
        return True
    
    def run(self):
        if not self.initialized:
            logger.error("System not ready")
            return
        
        logger.info("Running...")
        self.running = True
        self.start_time = time.time()
        
        try:
            while self.running:
                frame = self.camera.capture_frame()
                if frame is None:
                    time.sleep(0.01)
                    continue
                
                detections = self.detector.detect_humans(frame)
                target = self.tracker.update_target(detections)
                
                if target:
                    pan, tilt = self.tracker.get_servo_angles()
                    self.servo.set_target_position(pan, tilt)
                    
                    if self.tracker.is_target_centered():
                        self.laser.turn_on()
                    else:
                        self.laser.turn_off()
                else:
                    self.laser.turn_off()
                
                # Debug display
                if self.config.get('system', {}).get('save_video', False):
                    display = self.detector.draw_detections(frame, detections)
                    if target:
                        info = self.tracker.get_target_info()
                        text = f"Pan: {info['servo_angles']['pan']:.1f}° Tilt: {info['servo_angles']['tilt']:.1f}°"
                        cv2.putText(display, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    cv2.imshow('AutoRedL', display)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
                # Serial status
                if self.serial and self.serial.is_connected and self.frame_count % 30 == 0:
                    status = {
                        "frame_count": self.frame_count,
                        "has_target": target is not None,
                        "laser_on": self.laser.is_laser_on()
                    }
                    if target:
                        pan, tilt = self.tracker.get_servo_angles()
                        status.update({
                            "target_confidence": target.confidence,
                            "servo_angles": {"pan": pan, "tilt": tilt}
                        })
                    self.serial.send_status(status)
                
                self.frame_count += 1
                max_fps = self.config.get('system', {}).get('max_fps', 30)
                time.sleep(max(0, 1.0/max_fps))
                
        except KeyboardInterrupt:
            logger.info("Interrupted")
        finally:
            self.shutdown()
    
    def shutdown(self, signum=None, frame=None):
        logger.info("Shutting down...")
        self.running = False
        
        if self.laser:
            self.laser.emergency_stop()
            self.laser.release()
        
        if self.servo:
            self.servo.center_servos()
            time.sleep(0.5)
            self.servo.release()
        
        if self.camera:
            self.camera.release()
        
        if self.serial:
            self.serial.disconnect()
        
        cv2.destroyAllWindows()
        
        if self.frame_count > 0:
            elapsed = time.time() - self.start_time
            fps = self.frame_count / elapsed
            logger.info(f"Stats: {self.frame_count} frames, {elapsed:.1f}s, {fps:.1f} FPS")
        
        logger.info("Shutdown complete")


def main():
    logger.info("AutoRedL - Human Tracking Laser")
    
    system = AutoRedLSystem()
    
    if not system.initialize():
        logger.error("Init failed")
        sys.exit(1)
    
    system.run()


if __name__ == "__main__":
    main()
