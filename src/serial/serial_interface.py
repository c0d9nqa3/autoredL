import serial
import threading
import time
import json
from loguru import logger
from queue import Queue


class SerialInterface:
    def __init__(self, port="/dev/ttyUSB0", baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.running = False
        self.read_thread = None
        self.write_queue = Queue()
        self.write_thread = None
        self.command_callbacks = {}
        self.system_status = {}
        self.is_connected = False
    
    def connect(self):
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1.0)
            if self.serial_conn.is_open:
                self.is_connected = True
                self.running = True
                self.read_thread = threading.Thread(target=self.read_loop, daemon=True)
                self.write_thread = threading.Thread(target=self.write_loop, daemon=True)
                self.read_thread.start()
                self.write_thread.start()
                return True
        except Exception:
            pass
        return False
    
    def disconnect(self):
        self.running = False
        if self.read_thread:
            self.read_thread.join(timeout=1.0)
        if self.write_thread:
            self.write_thread.join(timeout=1.0)
        if self.serial_conn:
            self.serial_conn.close()
        self.is_connected = False
    
    def send_message(self, msg_type, data):
        if not self.is_connected:
            return
        
        message = {"timestamp": time.time(), "type": msg_type, "data": data}
        try:
            self.write_queue.put((json.dumps(message) + "\n").encode('utf-8'))
        except Exception:
            pass
    
    def send_status(self, status_data):
        self.system_status.update(status_data)
        self.send_message("STATUS", self.system_status)
    
    def register_command(self, command, callback):
        self.command_callbacks[command] = callback
    
    def read_loop(self):
        buffer = ""
        while self.running:
            try:
                if self.serial_conn and self.serial_conn.in_waiting > 0:
                    data = self.serial_conn.read(self.serial_conn.in_waiting).decode('utf-8', errors='ignore')
                    buffer += data
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        self.process_command(line.strip())
                time.sleep(0.01)
            except Exception:
                time.sleep(0.1)
    
    def write_loop(self):
        while self.running:
            try:
                if not self.write_queue.empty():
                    data = self.write_queue.get(timeout=0.1)
                    if self.serial_conn and self.serial_conn.is_open:
                        self.serial_conn.write(data)
                        self.serial_conn.flush()
                else:
                    time.sleep(0.01)
            except Exception:
                time.sleep(0.1)
    
    def process_command(self, command_line):
        if not command_line:
            return
        
        try:
            if command_line.startswith('{'):
                command_data = json.loads(command_line)
                command = command_data.get('command')
                params = command_data.get('params', {})
            else:
                parts = command_line.split(' ', 1)
                command = parts[0].upper()
                params = {'args': parts[1] if len(parts) > 1 else ''}
            
            if command in self.command_callbacks:
                result = self.command_callbacks[command](params)
                self.send_message("RESULT", {"command": command, "result": result})
        except Exception:
            pass


class SerialDebugger:
    def __init__(self, serial_interface):
        self.serial = serial_interface
        self.setup_commands()
    
    def setup_commands(self):
        commands = {
            "STATUS": self.cmd_status,
            "SERVO": self.cmd_servo,
            "LASER": self.cmd_laser,
            "STOP": self.cmd_stop
        }
        for cmd, callback in commands.items():
            self.serial.register_command(cmd, callback)
    
    def set_system_components(self, camera=None, servo=None, laser=None, detector=None, tracker=None):
        self.camera = camera
        self.servo = servo
        self.laser = laser
        self.detector = detector
        self.tracker = tracker
    
    def cmd_status(self, params):
        status = {
            "camera": self.camera.is_initialized if self.camera else False,
            "servo": self.servo.is_initialized if self.servo else False,
            "laser": self.laser.is_initialized if self.laser else False,
        }
        if self.servo and self.servo.is_initialized:
            pan, tilt = self.servo.get_current_position()
            status["servo_position"] = {"pan": pan, "tilt": tilt}
        if self.tracker:
            status["tracker"] = self.tracker.get_target_info()
        return status
    
    def cmd_servo(self, params):
        if not self.servo:
            return "No servo"
        args = params.get('args', '').split()
        if len(args) >= 2:
            try:
                pan, tilt = float(args[0]), float(args[1])
                self.servo.set_target_position(pan, tilt)
                return f"Moving to {pan}°, {tilt}°"
            except ValueError:
                return "Invalid args"
        else:
            pan, tilt = self.servo.get_current_position()
            return f"Position: {pan:.1f}°, {tilt:.1f}°"
    
    def cmd_laser(self, params):
        if not self.laser:
            return "No laser"
        args = params.get('args', '').lower()
        if args == 'on':
            self.laser.turn_on()
            return "Laser ON"
        elif args == 'off':
            self.laser.turn_off()
            return "Laser OFF"
        else:
            return "ON" if self.laser.is_laser_on() else "OFF"
    
    def cmd_stop(self, params):
        if self.laser:
            self.laser.emergency_stop()
        if self.servo:
            self.servo.center_servos()
        return "STOP"

