import time
import threading
from loguru import logger

try:
    import RPi.GPIO as GPIO
except ImportError:
    class MockGPIO:
        BCM = "BCM"
        OUT = "OUT"
        HIGH = 1
        LOW = 0
        @staticmethod
        def setmode(mode): pass
        @staticmethod
        def setup(pin, mode): pass
        @staticmethod
        def output(pin, state): pass
        @staticmethod
        def cleanup(): pass
    
    GPIO = MockGPIO()


class LaserController:
    def __init__(self, enable_pin=20, safety_timeout=5.0):
        self.enable_pin = enable_pin
        self.safety_timeout = safety_timeout
        self.is_on = False
        self.is_initialized = False
        self.last_on_time = 0.0
        self.safety_thread = None
        self.safety_running = False
        self.lock = threading.Lock()
    
    def initialize(self):
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.enable_pin, GPIO.OUT)
            GPIO.output(self.enable_pin, GPIO.LOW)
            
            self.safety_running = True
            self.safety_thread = threading.Thread(target=self.safety_monitor, daemon=True)
            self.safety_thread.start()
            
            self.is_initialized = True
            return True
        except Exception:
            return False
    
    def turn_on(self):
        if not self.is_initialized:
            return False
        
        with self.lock:
            if not self.is_on:
                GPIO.output(self.enable_pin, GPIO.HIGH)
                self.is_on = True
                self.last_on_time = time.time()
            return True
    
    def turn_off(self):
        if not self.is_initialized:
            return False
        
        with self.lock:
            if self.is_on:
                GPIO.output(self.enable_pin, GPIO.LOW)
                self.is_on = False
            return True
    
    def is_laser_on(self):
        with self.lock:
            return self.is_on
    
    def emergency_stop(self):
        with self.lock:
            GPIO.output(self.enable_pin, GPIO.LOW)
            self.is_on = False
    
    def safety_monitor(self):
        while self.safety_running:
            with self.lock:
                if self.is_on and (time.time() - self.last_on_time) > self.safety_timeout:
                    GPIO.output(self.enable_pin, GPIO.LOW)
                    self.is_on = False
            time.sleep(0.1)
    
    def get_on_duration(self):
        with self.lock:
            return time.time() - self.last_on_time if self.is_on else 0.0
    
    def release(self):
        self.safety_running = False
        if self.safety_thread:
            self.safety_thread.join(timeout=1.0)
        self.turn_off()
        GPIO.cleanup()
        self.is_initialized = False

