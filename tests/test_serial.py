#!/usr/bin/env python3
"""
Serial interface testing script for AutoRedL
"""

import time
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.serial.serial_interface import SerialInterface, SerialDebugger
from loguru import logger


def test_serial_interface():
    """Test serial interface functionality"""
    logger.info("Testing serial interface...")
    
    # Try common serial ports
    ports_to_try = [
        "/dev/ttyUSB0",   # USB-to-TTL on Linux
        "/dev/ttyACM0",   # Arduino/USB CDC on Linux
        "/dev/ttyS0",     # Hardware UART on Linux
        "COM3",           # Windows
        "COM4",           # Windows
    ]
    
    serial_conn = None
    
    # Try to connect to available port
    for port in ports_to_try:
        try:
            serial_conn = SerialInterface(port=port, baudrate=115200)
            if serial_conn.connect():
                logger.info(f"Connected to {port}")
                break
        except Exception as e:
            logger.debug(f"Failed to connect to {port}: {e}")
    
    if not serial_conn or not serial_conn.is_connected:
        logger.warning("No serial port available, running simulation mode")
        return test_serial_simulation()
    
    # Setup debugger
    debugger = SerialDebugger(serial_conn)
    
    # Send test messages
    logger.info("Sending test messages...")
    
    serial_conn.send_message("INFO", "Serial test started")
    serial_conn.send_status({
        "system": "running",
        "test_mode": True,
        "timestamp": time.time()
    })
    
    # Test commands
    test_commands = [
        "STATUS",
        "HELP",
        "SERVO 0 0",
        "LASER off"
    ]
    
    for cmd in test_commands:
        logger.info(f"Testing command: {cmd}")
        # Simulate command processing
        try:
            parts = cmd.split(' ', 1)
            command = parts[0]
            params = {'args': parts[1] if len(parts) > 1 else ''}
            
            if hasattr(debugger, f'cmd_{command.lower()}'):
                result = getattr(debugger, f'cmd_{command.lower()}')(params)
                logger.info(f"Command result: {result}")
            
        except Exception as e:
            logger.error(f"Command error: {e}")
        
        time.sleep(1)
    
    # Keep connection open for interactive testing
    logger.info("Serial interface ready. You can now send commands from another terminal.")
    logger.info("Available commands: STATUS, HELP, SERVO <pan> <tilt>, LASER on/off")
    logger.info("Press Ctrl+C to exit")
    
    try:
        while True:
            # Send periodic status
            serial_conn.send_status({
                "uptime": time.time(),
                "status": "running"
            })
            time.sleep(5)
            
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    
    finally:
        serial_conn.disconnect()
    
    return True


def test_serial_simulation():
    """Test serial interface in simulation mode"""
    logger.info("Running serial interface simulation...")
    
    # Create serial interface (won't actually connect)
    serial_conn = SerialInterface("/dev/null", 115200)
    debugger = SerialDebugger(serial_conn)
    
    # Test command processing
    test_commands = [
        ("STATUS", {}),
        ("HELP", {}),
        ("SERVO", {"args": "45 30"}),
        ("LASER", {"args": "on"}),
        ("LASER", {"args": "off"}),
    ]
    
    for cmd, params in test_commands:
        logger.info(f"Testing command: {cmd} with params: {params}")
        
        try:
            if hasattr(debugger, f'cmd_{cmd.lower()}'):
                result = getattr(debugger, f'cmd_{cmd.lower()}')(params)
                logger.info(f"Command result: {result}")
            else:
                logger.warning(f"Command {cmd} not found")
                
        except Exception as e:
            logger.error(f"Command error: {e}")
    
    logger.info("Serial simulation test completed")
    return True


if __name__ == "__main__":
    test_serial_interface()

