#!/usr/bin/env python3
"""
Servo testing script for AutoRedL
"""

import time
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.servo.servo_controller import ServoController
from loguru import logger


def test_servo():
    """Test servo functionality"""
    logger.info("Testing servo controller...")
    
    # Initialize servo controller
    servo = ServoController(pan_pin=18, tilt_pin=19, frequency=50)
    
    if not servo.initialize():
        logger.error("Servo initialization failed")
        return False
    
    logger.info("Servo controller initialized successfully")
    
    try:
        # Test sequence
        test_positions = [
            (0, 0),      # Center
            (45, 0),     # Right
            (0, 30),     # Up
            (-45, 0),    # Left
            (0, -30),    # Down
            (30, 20),    # Right-Up
            (-30, -20),  # Left-Down
            (0, 0)       # Center again
        ]
        
        for i, (pan, tilt) in enumerate(test_positions):
            logger.info(f"Moving to position {i+1}/{len(test_positions)}: Pan={pan}°, Tilt={tilt}°")
            servo.set_target_position(pan, tilt)
            
            # Wait for movement to complete
            time.sleep(2.0)
            
            current_pan, current_tilt = servo.get_current_position()
            logger.info(f"Current position: Pan={current_pan:.1f}°, Tilt={current_tilt:.1f}°")
        
        # Smooth sweep test
        logger.info("Performing smooth sweep test...")
        for angle in range(-45, 46, 5):
            servo.set_target_position(angle, 0)
            time.sleep(0.2)
        
        # Return to center
        servo.set_target_position(0, 0)
        time.sleep(2.0)
        
        logger.info("Servo test completed successfully")
        
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    
    finally:
        servo.center_servos()
        time.sleep(1.0)
        servo.release()
    
    return True


if __name__ == "__main__":
    test_servo()

