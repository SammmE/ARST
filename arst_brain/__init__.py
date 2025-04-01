import cv2
import numpy as np

from .YOLOv12Detector import YOLOv12Detector


class ARST:
    def __init__(self):
        # Initialize internal state, load models, etc.
        self.current_frame = None
        self.detector = YOLOv12Detector()

    def update_video_feed(self, video_frame: bytes):
        """
        Update the latest video frame.
        Decode the JPEG bytes as a color image, resize it to the model’s expected dimensions,
        run object detection, and overlay the detection boxes and labels.
        """
        # Decode JPEG bytes into a 3-channel BGR image.
        self.current_frame = cv2.imdecode(
            np.frombuffer(video_frame, np.uint8), cv2.IMREAD_COLOR
        )
        if self.current_frame is None:
            return

        # Resize the frame to 640x640 (or whichever size your model expects)
        resized_frame = cv2.resize(self.current_frame, (640, 640))

        # Run detection on the resized frame.
        detections = self.detector.detect(resized_frame)

        # Draw detections on the resized frame.
        for detection in detections:
            label = detection["label"]
            bbox = detection["bbox"]
            # bbox is assumed to be [x1, y1, x2, y2]
            cv2.rectangle(
                resized_frame,
                (int(bbox[0]), int(bbox[1])),
                (int(bbox[2]), int(bbox[3])),
                (0, 255, 0),
                2,
            )
            cv2.putText(
                resized_frame,
                label,
                (int(bbox[0]), int(bbox[1]) - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2,
            )

        # Optionally, update self.current_frame to the processed (resized with overlays) image.
        self.current_frame = resized_frame

    def process_meta(self, payload: dict) -> list:
        """
        Process the meta payload and return a list of instructions.

        Expected payload structure:
            {
                "is_active": bool,
                "active_prompt": str
            }

        The method can use self.current_frame to help make decisions.
        """
        instructions = []

        if payload.get("is_active"):
            prompt = payload.get("active_prompt", "")
            # Example logic: when active, execute the provided prompt.
            instructions.append(f"Execute active prompt: {prompt}")
        else:
            # When not active, perhaps just continue idle scanning.
            instructions.append("Continue idle scanning")

        # More complex decision logic using self.current_frame can be added here.
        return instructions
