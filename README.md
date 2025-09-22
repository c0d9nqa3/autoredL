# AutoRedL - Autonomous Human Tracking Laser System

## Project Overview

AutoRedL is an embedded AI system designed to automatically detect and track human targets using computer vision, with a laser pointer that continuously follows the detected person. The system is built around the Orange Pi Zero 3 single-board computer and features a two-degree-of-freedom gimbal for precise laser positioning.

## System Architecture

### Hardware Components

| Category | Component | Quantity | Status |
|----------|-----------|----------|--------|
| Core Controller | Orange Pi Zero 3 (1GB) | 1 | Active |
| Vision System | 2-DOF Gimbal Kit with 100W CSI Camera | 1 | Active |
| Actuators | MG90S Metal Gear Servo Motors | 2 | Integrated |
| Targeting | 650nm Red Laser Module (30mW) | 1 | Active |
| Circuit Base | Breadboard + Dupont Wires (Female-to-Female) | 1 Set | Active |
| Power Supply | 18650 Battery Holder (2-Cell Series, with Switch) | 1 | Active |
| Voltage Regulation | AMS1117-5V Voltage Regulator Module | 1 | Active |
| Energy Storage | 18650 Rechargeable Lithium Batteries | 2 | Active |
| Main Power | 5V/2A DC Power Adapter | 1 | Active |
| Storage | 16GB+ TF (MicroSD) Card | 1 | Active |
| Debug Interface | USB-to-TTL Serial Module (CH340/CP2102) | 1 | Active |

### System Block Diagram

```
[18650 Batteries] → [AMS1117-5V] → [Power Distribution]
                                              ↓
[CSI Camera] → [Orange Pi Zero 3] → [Servo Control] → [2-DOF Gimbal]
     ↓                    ↓
[Vision Processing] → [Target Detection] → [Laser Control] → [Laser Module]
```

## Technical Specifications

### Hardware Specifications
- **Processor**: Orange Pi Zero 3 (H618 Quad-core ARM Cortex-A53)
- **Memory**: 1GB LPDDR3 RAM
- **Camera**: 100W CSI interface camera module
- **Servo Motors**: MG90S (4.8V-6V, 1.8kg·cm torque)
- **Laser**: 650nm red laser, 30mW output power
- **Power**: 7.4V (2×18650) with 5V regulation
- **Operating System**: Orange Pi OS (Linux-based)

### Software Stack
- **Operating System**: Orange Pi OS
- **Programming Language**: Python 3.x
- **Computer Vision**: OpenCV 4.x
- **Hardware Control**: RPi.GPIO
- **AI Framework**: TensorFlow Lite / ONNX Runtime
- **Target Detection**: YOLOv5/v8 or MobileNet-SSD

## Key Features

### Real-time Human Detection
- Advanced computer vision algorithms for human body detection
- Optimized for embedded systems with limited computational resources
- Configurable detection sensitivity and tracking parameters

### Precise Target Tracking
- Two-degree-of-freedom gimbal system for smooth tracking
- PID control algorithm for accurate positioning
- Real-time coordinate transformation and servo control

### Laser Targeting System
- Synchronized laser pointer that follows detected targets
- Safety features including power control and beam management
- Adjustable laser intensity and targeting precision

### Embedded AI Processing
- On-device inference for real-time performance
- Optimized neural network models for ARM architecture
- Low-latency processing pipeline

## System Requirements

### Hardware Requirements
- Orange Pi Zero 3 development board
- Compatible CSI camera module
- Two MG90S servo motors
- 650nm laser module with appropriate power rating
- Power management system (18650 batteries + voltage regulator)
- Breadboard and connecting wires

### Software Requirements
- Orange Pi OS or compatible Linux distribution
- Python 3.7 or higher
- OpenCV 4.x
- Required Python packages (see requirements.txt)

## Safety Considerations

### Laser Safety
- 30mW laser power requires appropriate safety measures
- Never point laser directly at eyes or reflective surfaces
- Implement physical and software safety switches
- Use appropriate laser safety goggles during development

### Electrical Safety
- Proper voltage regulation to prevent component damage
- Correct polarity connections for all components
- Adequate power supply capacity for all connected devices
- Proper grounding and circuit protection

## Performance Metrics

### Detection Performance
- Detection range: 2-10 meters (depending on lighting conditions)
- Detection accuracy: >90% in optimal conditions
- Processing latency: <100ms per frame
- Tracking smoothness: 30 FPS target

### System Performance
- Power consumption: <5W total system power
- Operating temperature: -10°C to +60°C
- Battery life: 2-4 hours continuous operation
- Servo response time: <50ms for 90-degree movement

## License

This project is open source. Please refer to the license file for detailed terms and conditions.
