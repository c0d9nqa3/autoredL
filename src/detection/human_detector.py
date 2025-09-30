import cv2
import numpy as np
from typing import List, Tuple, Optional, Dict
from loguru import logger
import time

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False


class BoundingBox:
    def __init__(self, x: float, y: float, width: float, height: float, confidence: float, class_id: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.confidence = confidence
        self.class_id = class_id
    
    @property
    def center(self):
        return (self.x + self.width / 2, self.y + self.height / 2)
    
    @property
    def area(self):
        return self.width * self.height
    
    def to_dict(self):
        return {
            'x': self.x, 'y': self.y, 'width': self.width, 'height': self.height,
            'confidence': self.confidence, 'class_id': self.class_id,
            'center': self.center, 'area': self.area
        }


class HumanDetector:
    def __init__(self, model_path="models/yolov5s.onnx", confidence_threshold=0.5,
                 nms_threshold=0.4, input_size=(640, 640)):
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.nms_threshold = nms_threshold
        self.input_size = input_size
        
        self.session = None
        self.input_name = None
        self.output_names = None
        self.is_initialized = False
    
    def initialize(self):
        if not ONNX_AVAILABLE:
            return False
        
        try:
            providers = ['CPUExecutionProvider']
            if ort.get_device() == 'GPU':
                providers.insert(0, 'CUDAExecutionProvider')
            
            self.session = ort.InferenceSession(self.model_path, providers=providers)
            self.input_name = self.session.get_inputs()[0].name
            self.output_names = [output.name for output in self.session.get_outputs()]
            
            self.is_initialized = True
            return True
        except Exception:
            return False
    
    def preprocess_frame(self, frame):
        input_frame = cv2.resize(frame, self.input_size)
        input_frame = cv2.cvtColor(input_frame, cv2.COLOR_BGR2RGB)
        input_frame = input_frame.astype(np.float32) / 255.0
        input_frame = np.transpose(input_frame, (2, 0, 1))
        return np.expand_dims(input_frame, axis=0)
    
    def postprocess_outputs(self, outputs, original_shape):
        predictions = outputs[0][0]  # Remove batch dimension
        scale_x = original_shape[1] / self.input_size[0]
        scale_y = original_shape[0] / self.input_size[1]
        
        boxes, confidences, class_ids = [], [], []
        
        for detection in predictions:
            center_x, center_y, width, height = detection[:4]
            confidence = detection[4]
            class_scores = detection[5:]
            
            class_id = np.argmax(class_scores)
            class_confidence = class_scores[class_id]
            overall_confidence = confidence * class_confidence
            
            # Only person class (class_id == 0)
            if overall_confidence > self.confidence_threshold and class_id == 0:
                x = (center_x - width / 2) * scale_x
                y = (center_y - height / 2) * scale_y
                w = width * scale_x
                h = height * scale_y
                
                boxes.append([x, y, w, h])
                confidences.append(float(overall_confidence))
                class_ids.append(int(class_id))
        
        detections = []
        if boxes:
            indices = cv2.dnn.NMSBoxes(boxes, confidences, 
                                     self.confidence_threshold, self.nms_threshold)
            if len(indices) > 0:
                for i in indices.flatten():
                    x, y, w, h = boxes[i]
                    detections.append(BoundingBox(x, y, w, h, confidences[i], class_ids[i]))
        
        return detections
    
    def detect_humans(self, frame):
        if not self.is_initialized:
            return []
        
        try:
            input_frame = self.preprocess_frame(frame)
            outputs = self.session.run(self.output_names, {self.input_name: input_frame})
            return self.postprocess_outputs(outputs, frame.shape[:2])
        except Exception:
            return []
    
    def get_largest_detection(self, detections):
        return max(detections, key=lambda det: det.area) if detections else None
    
    def draw_detections(self, frame, detections):
        result = frame.copy()
        for det in detections:
            x, y, w, h = int(det.x), int(det.y), int(det.width), int(det.height)
            cv2.rectangle(result, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            cx, cy = det.center
            cv2.circle(result, (int(cx), int(cy)), 5, (0, 0, 255), -1)
            
            label = f"Person: {det.confidence:.2f}"
            cv2.putText(result, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return result


class FallbackDetector:
    def __init__(self):
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        self.is_initialized = True
    
    def initialize(self):
        return True
    
    def detect_humans(self, frame):
        try:
            boxes, weights = self.hog.detectMultiScale(frame, winStride=(8, 8), padding=(32, 32), scale=1.05)
            detections = []
            for i, (x, y, w, h) in enumerate(boxes):
                confidence = weights[i][0] if len(weights) > i else 0.5
                detections.append(BoundingBox(x, y, w, h, confidence, 0))
            return detections
        except Exception:
            return []
    
    def get_largest_detection(self, detections):
        return max(detections, key=lambda det: det.area) if detections else None
    
    def draw_detections(self, frame, detections):
        result = frame.copy()
        for det in detections:
            x, y, w, h = int(det.x), int(det.y), int(det.width), int(det.height)
            cv2.rectangle(result, (x, y), (x + w, y + h), (255, 0, 0), 2)
            cx, cy = det.center
            cv2.circle(result, (int(cx), int(cy)), 5, (0, 0, 255), -1)
        return result
