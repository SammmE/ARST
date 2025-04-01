# ARST: Autonomous Dual-Mode Robotic System
###### Recreation of the robot TARS from the movie Interstellar, but IDK anything about copyright so I'm calling it ARST

This is a recreation of TARS, the robot from the movie *Interstellar*. This repository contains the source code for ARST—a robotic system that can move, talk, and respond to voice commands in two distinct modes.

---

## What is ARST?

ARST is an advanced robotic system designed to operate in two distinct modes—**Idle** and **Active**—to intelligently interact with its environment and respond to human commands.

### Idle Mode
In this mode, ARST continuously scans its surroundings using state-of-the-art object detection and sensor fusion. It:
- Logs detected objects.
- Tracks the duration since each object was last seen.
- Autonomously navigates using pathfinding and obstacle avoidance to reacquire lost objects.
- Listens for its activation trigger (its name) to transition into Active mode.

![Idle Mode Workflow](./images/idle.svg)

### Active Mode
Once activated, ARST switches to Active mode where it processes and executes human commands. Leveraging a powerful LLM instruct model, the system:
- Interprets natural language commands.
- Calls appropriate functions (e.g., providing system status, retrieving information, executing movement commands).
- Interacts with users in a natural, conversational manner.

![Active Mode Workflow](./images/active.svg)

---

## Programming Side

The system is split into three main components:

1. **Communication (Rust)**
   - **Responsibilities:**  
     - Receive video footage and sensor data from the Arduino.
     - Process video frames using the `VideoProcessor`.
     - Aggregate sensor data via the `SensorAggregator`.
     - Handle bidirectional messaging using the `CommunicationHandler`.
     - Expose a real-time data stream to the Dashboard through REST/WebSocket APIs.
   - **Key Points:**  
     - Performance-critical tasks (like video encoding and real-time sensor data handling) are implemented in Rust for efficiency.
     - Data is packaged into a JSON-based protocol for communication.

2. **Brain (Python)**
   - **Responsibilities:**  
     - Perform image recognition using modules like `ImageRecognizer` (leveraging OpenCV and deep learning libraries).
     - Generate and send prompts to an instruct model (Ollama) via the `InstructModelInterface`.
     - Use the `DecisionEngine` to combine sensor data and image recognition results, then output the best decision.
     - Continuously improve its decision-making via the `OnlineLearner`.
   - **Key Points:**  
     - Uses a combination of Python for AI/decision-making tasks.
     - Integrates seamlessly with the instruct model to process commands and generate actions.

3. **Dashboard (Python Web Service)**
   - **Responsibilities:**  
     - Display real-time sensor data, video feeds, and decision outputs.
     - Provide a user interface for monitoring system status and logs.
     - Allow manual overrides or adjustments if necessary.
   - **Key Points:**  
     - Built using Flask (or a similar framework) to render live updates and logs.
     - Collects data from the Communication module via REST/WebSocket endpoints.

---

## In-Depth Current Plan

- **Hardware Integration:**  
  - The Arduino captures video and sensor data.
  - Communication between the Arduino and the main processing system is managed directly (no MCP), using a lightweight JSON-based protocol.
  
- **Data Flow and Decision Making:**  
  - **Step 1:** Arduino sends video and sensor data to the Rust Communication module.
  - **Step 2:** The Communication module processes and forwards this data to the Python Brain.
  - **Step 3:** The Brain performs image recognition and constructs a prompt by merging sensor data with recognized objects.
  - **Step 4:** The instruct model (Ollama) processes the prompt and returns a decision.
  - **Step 5:** The decision is sent back through the Communication module, which updates the Dashboard and commands the Arduino to execute actions.
  
- **Online Learning:**  
  - The Brain continuously updates its models via an online learning loop to refine decision-making capabilities based on new data.

For more detail, please refer to the mermaid diagrams in the repository which illustrate the data and decision flow.

---

## Workflow

The entire system workflow is orchestrated through the interaction of the three main components:

- **Data Capture & Pre-Processing (Arduino → Communication):**  
  - Video footage and sensor readings are captured and pre-processed.
- **Decision Making (Communication → Brain):**  
  - The pre-processed data is sent to the Brain which handles image recognition, prompt generation, and decision-making using an instruct model.
- **Feedback & Command Execution (Brain → Communication → Arduino):**  
  - The Brain's decision is relayed back to the Communication module, which then updates the Dashboard and issues commands back to the Arduino.

Refer to the following mermaid diagrams available in the repository for a visual overview:
**Idle Mode Workflow:**
<br></br>
[![](https://mermaid.ink/img/pako:eNpNkMtuwjAQRX_FmkVXAZUk5LWoFBIqVSoVEnTThIWbDIlFYiMzKQXEv9eEh-qVxz5HvtcnKFSJEMG6Ufui5prYMs0lMyvOFnSZ38oG2bzmO1yxweCFTbKZkoKUZnH7LVASSznx1VWa9EiSxZI3hyOytcGSTgu1E3RgT2zOiVDL3Q1PejzNPrclJ2TvyLUUsmIzE6oxeGxoSUJJtthyeZPSXppmSY3Fpn9hqUVVoTYp9SXmFZsa7HGTImFBWPbqa7bYCypqRorFBYmfe79_4od6uH3pXIIFLeqWi9J81-mC5kA1tphDZLYl15sccnk2HO9ILQ6ygIh0hxZo1VU1RGve7MzU9WVTwSvN28ep6felVHtXzAjRCX4hsoNg6Ix8z_bCsTOyxxYcIHK9Yeg-u47vjLwgdMfO2YJjrz-bCzfwvdC2ndAfOa5jQaUvoW9ZUJaoE9VJgiiwz3_IYp8l?type=png)](https://mermaid.live/edit#pako:eNpNkMtuwjAQRX_FmkVXAZUk5LWoFBIqVSoVEnTThIWbDIlFYiMzKQXEv9eEh-qVxz5HvtcnKFSJEMG6Ufui5prYMs0lMyvOFnSZ38oG2bzmO1yxweCFTbKZkoKUZnH7LVASSznx1VWa9EiSxZI3hyOytcGSTgu1E3RgT2zOiVDL3Q1PejzNPrclJ2TvyLUUsmIzE6oxeGxoSUJJtthyeZPSXppmSY3Fpn9hqUVVoTYp9SXmFZsa7HGTImFBWPbqa7bYCypqRorFBYmfe79_4od6uH3pXIIFLeqWi9J81-mC5kA1tphDZLYl15sccnk2HO9ILQ6ygIh0hxZo1VU1RGve7MzU9WVTwSvN28ep6felVHtXzAjRCX4hsoNg6Ix8z_bCsTOyxxYcIHK9Yeg-u47vjLwgdMfO2YJjrz-bCzfwvdC2ndAfOa5jQaUvoW9ZUJaoE9VJgiiwz3_IYp8l)
<br></br>
**Active Mode Workflow:** 
<br></br>
- [![](https://mermaid.ink/img/pako:eNpdkF1vgjAYhf9K816jE0E-erFFRZclupm5mw28aKAKmbSmH5uO8N9XEMyyXvU9zzlvTltByjMKGPZH_p3mRCj0FiUMmTONt6qZp6kqvija5ETSHRoM7tEsfqUpbcSGcYZWhVS7a2rWOubxhkjZYYkUR6vVGu25QBFNC2nEzj5v7dFtYWN70eqk1V23-18gagOLeHGmqVZ9gw4uWris1lz0RD7UV7Y0DL1Tee33R3vmrfRoOigtWFP2KTv2D04YWFBSUZIiM99UNcEEVE5LmgA214yIzwQSVhsf0YpvLywFrISmFgiuDzngPTlKM-lTRhSNCnIQpLypJ8I-OC_7iBkBV3AGPA6CoWP73tgLJ449nlhwAex6w9AduY7v2F4QuhOntuCnjY8McAPfC43XD71R4FlwEE3prgtlGRVzrpkCHLj1L7MJmio?type=png)](https://mermaid.live/edit#pako:eNpdkF1vgjAYhf9K816jE0E-erFFRZclupm5mw28aKAKmbSmH5uO8N9XEMyyXvU9zzlvTltByjMKGPZH_p3mRCj0FiUMmTONt6qZp6kqvija5ETSHRoM7tEsfqUpbcSGcYZWhVS7a2rWOubxhkjZYYkUR6vVGu25QBFNC2nEzj5v7dFtYWN70eqk1V23-18gagOLeHGmqVZ9gw4uWris1lz0RD7UV7Y0DL1Tee33R3vmrfRoOigtWFP2KTv2D04YWFBSUZIiM99UNcEEVE5LmgA214yIzwQSVhsf0YpvLywFrISmFgiuDzngPTlKM-lTRhSNCnIQpLypJ8I-OC_7iBkBV3AGPA6CoWP73tgLJ449nlhwAex6w9AduY7v2F4QuhOntuCnjY8McAPfC43XD71R4FlwEE3prgtlGRVzrpkCHLj1L7MJmio)
<br></br>
- **System Architecture & Data Flow:** See the detailed diagram in the documentation folder.

---

## Future Plans

- **Enhanced Learning:**  
  - Integrate advanced reinforcement learning techniques for improved adaptive behavior.
- **Additional Sensors:**  
  - Incorporate more diverse environmental sensors for richer context and improved decision-making.
- **Modular Expansion:**  
  - Develop additional plug-and-play modules for specialized tasks (e.g., advanced obstacle avoidance, remote operation).
- **Optimization:**  
  - Optimize the Rust components further for better performance in video processing and data handling.
- **User Interface Enhancements:**  
  - Expand the Dashboard functionalities to include historical data analysis, system diagnostics, and user customization options.
- **Documentation & Open Source Collaboration:**  
  - Improve project documentation and encourage community contributions for continuous improvement.

---

## License

*This project is provided as-is. For questions regarding copyright, please consult the repository owner.*

---

## Contributing

Contributions, issues, and feature requests are welcome!  
Feel free to check the [issues page](./issues) if you want to contribute.

---

## Acknowledgements

- Inspired by the robot TARS from *Interstellar*.
- Thanks to the communities behind Rust, Python, and the various open-source libraries and frameworks used in this project.

---

*Happy coding and robotics building!*
