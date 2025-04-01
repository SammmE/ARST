import urllib.request
import os
from ultralytics import YOLO


def patch_attn_modules(model):
    """
    Monkey-patch all AAttn modules in the model so that if an instance does not have
    a 'qkv' attribute, we assign its 'qk' attribute to 'qkv'.
    """
    for module in model.modules():
        # Check for the attention module by its class name (could be 'AAttn' or similar)
        if module.__class__.__name__ == "AAttn":
            if not hasattr(module, "qkv"):
                # Patch: assign qk as qkv so that the forward pass works.
                module.qkv = module.qk
                print(f"Patched {module} by setting 'qkv' attribute to 'qk'")
    return model


class YOLOv12Detector:
    def __init__(self, model_path="yolov12.pt"):
        if not os.path.exists(model_path):
            # Download the model from the internet.
            url = "https://github.com/sunsmarterjie/yolov12/releases/download/turbo/yolov12n.pt"
            urllib.request.urlretrieve(url, model_path)
        self.model = YOLO(model_path)
        # Patch the model's attention modules if needed.
        patch_attn_modules(self.model)

    def detect(self, frame):
        """
        Process the given frame (a numpy array) and return a list of detections.
        Each detection is represented as a dict, for example:
            {
                "label": "person",
                "confidence": 0.9,
                "bbox": [x1, y1, x2, y2]
            }
        """
        results = self.model(frame)
        detections = []
        # Get the first result.
        result = results[0]
        # Iterate over detected boxes.
        for box in result.boxes:
            # Extract bounding box coordinates.
            xyxy = box.xyxy[0].tolist()
            # Get confidence and class index.
            conf = box.conf.item() if box.conf is not None else 0
            cls = int(box.cls.item())
            # Convert class index to label using the model's names.
            label = (
                self.model.names.get(cls, str(cls))
                if hasattr(self.model, "names")
                else str(cls)
            )
            detections.append({"label": label, "confidence": conf, "bbox": xyxy})
        return detections
