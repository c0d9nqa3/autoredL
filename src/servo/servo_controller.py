import time
import threading
from loguru import logger

try:
    import RPi.GPIO as GPIO
except ImportError:
    class MockGPIO:
        BCM = "BCM"
        OUT = "OUT"
        @staticmethod
        def setmode(mode): pass
        @staticmethod
        def setup(pin, mode): pass
        @staticmethod
        def PWM(pin, freq): return MockPWM()
        @staticmethod
        def cleanup(): pass
    
    class MockPWM:
        def start(self, duty): pass
        def ChangeDutyCycle(self, duty): pass
        def stop(self): pass
    
    GPIO = MockGPIO()


class PIDController:
    def __init__(self, kp=0.8, ki=0.1, kd=0.2, max_output=10.0):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.max_output = max_output
        self.last_error = 0.0
        self.integral = 0.0
        self.last_time = time.time()
    
    def update(self, error):
        current_time = time.time()
        dt = current_time - self.last_time
        
        if dt <= 0.0:
            return 0.0
        
        proportional = self.kp * error
        self.integral += error * dt
        integral = self.ki * self.integral
        derivative = self.kd * (error - self.last_error) / dt
        
        output = proportional + integral + derivative
        output = max(-self.max_output, min(self.max_output, output))
        
        self.last_error = error
        self.last_time = current_time
        return output
    
    def reset(self):
        self.last_error = 0.0
        self.integral = 0.0
        self.last_time = time.time()


class ServoController:
    def __init__(self, pan_pin=18, tilt_pin=19, frequency=50):
        self.pan_pin = pan_pin
        self.tilt_pin = tilt_pin
        self.frequency = frequency
        
        self.current_pan = 0.0
        self.current_tilt = 0.0
        self.target_pan = 0.0
        self.target_tilt = 0.0
        
        self.pan_min, self.pan_max = -90, 90
        self.tilt_min, self.tilt_max = -45, 45
        
        self.pan_pid = PIDController()
        self.tilt_pid = PIDController()
        
        self.pan_pwm = None
        self.tilt_pwm = None
        self.control_thread = None
        self.running = False
        self.lock = threading.Lock()
        self.is_initialized = False
    
    def initialize(self):
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pan_pin, GPIO.OUT)
            GPIO.setup(self.tilt_pin, GPIO.OUT)
            
            self.pan_pwm = GPIO.PWM(self.pan_pin, self.frequency)
            self.tilt_pwm = GPIO.PWM(self.tilt_pin, self.frequency)
            
            center_duty = self.angle_to_duty(0)
            self.pan_pwm.start(center_duty)
            self.tilt_pwm.start(center_duty)
            
            self.running = True
            self.control_thread = threading.Thread(target=self.control_loop, daemon=True)
            self.control_thread.start()
            
            self.is_initialized = True
            return True
        except Exception:
            return False
    
    def set_target_position(self, pan, tilt):
        with self.lock:
            self.target_pan = max(self.pan_min, min(self.pan_max, pan))
            self.target_tilt = max(self.tilt_min, min(self.tilt_max, tilt))
    
    def get_current_position(self):
        with self.lock:
            return self.current_pan, self.current_tilt
    
    def set_limits(self, pan_min, pan_max, tilt_min, tilt_max):
        self.pan_min, self.pan_max = pan_min, pan_max
        self.tilt_min, self.tilt_max = tilt_min, tilt_max
    
    def angle_to_duty(self, angle):
        pulse_width = 1.5 + (angle / 90.0) * 0.5
        return (pulse_width / (1000.0 / self.frequency)) * 100
    
    def control_loop(self):
        while self.running:
            try:
                with self.lock:
                    pan_error = self.target_pan - self.current_pan
                    tilt_error = self.target_tilt - self.current_tilt
                    
                    pan_output = self.pan_pid.update(pan_error)
                    tilt_output = self.tilt_pid.update(tilt_error)
                    
                    self.current_pan += pan_output
                    self.current_tilt += tilt_output
                    
                    self.current_pan = max(self.pan_min, min(self.pan_max, self.current_pan))
                    self.current_tilt = max(self.tilt_min, min(self.tilt_max, self.current_tilt))
                    
                    if self.pan_pwm and self.tilt_pwm:
                        self.pan_pwm.ChangeDutyCycle(self.angle_to_duty(self.current_pan))
                        self.tilt_pwm.ChangeDutyCycle(self.angle_to_duty(self.current_tilt))
                
                time.sleep(0.02)
            except Exception:
                time.sleep(0.1)
    
    def center_servos(self):
        self.set_target_position(0, 0)
    
    def release(self):
        self.running = False
        if self.control_thread:
            self.control_thread.join(timeout=1.0)
        if self.pan_pwm:
            self.pan_pwm.stop()
        if self.tilt_pwm:
            self.tilt_pwm.stop()
        GPIO.cleanup()
        self.is_initialized = False

