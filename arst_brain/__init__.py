# arst_brain/__init__.py


class ARST:
    def __init__(self):
        # Initialize internal state, load models, etc.
        self.current_frame = None

    def update_video_feed(self, video_frame: bytes):
        """
        Update the latest video frame.
        This frame can be used for decision making.
        """
        self.current_frame = video_frame

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
