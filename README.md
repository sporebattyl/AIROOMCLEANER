# AI Room Cleaner

## Description

AI Room Cleaner is a smart home application designed to analyze the cleanliness of a room using artificial intelligence. It captures an image from a designated camera, sends it to a powerful AI model (either OpenAI's GPT or Google's Gemini), and receives a list of "messes" or cleaning tasks. These tasks are then displayed on a simple, intuitive web interface, helping you identify what needs cleaning. The entire application is containerized with Docker, making it easy to set up and run, and it appears to be designed for seamless integration as a Home Assistant addon.

## Key Features

*   **AI-Powered Mess Detection:** Leverages generative AI to analyze room images and identify areas that require cleaning.
*   **Dual AI Model Support:** Supports both OpenAI and Google Generative AI models for flexibility.
*   **Web-Based Interface:** A clean and simple frontend allows users to trigger room analysis and view a list of cleaning tasks.
*   **Camera Integration:** Connects to a camera entity to fetch real-time images for analysis.
*   **Task List Generation:** Automatically generates a to-do list based on the AI's findings.
*   **Cleanliness Score:** Calculates and displays a "cleanliness score" to quickly gauge the room's state.
*   **Dockerized Deployment:** Comes with a `Dockerfile` for easy, consistent deployment across different environments.
*   **Home Assistant Ready:** The `run.sh` script uses `bashio`, indicating it's structured to work as a Home Assistant addon.

## Technology Stack

*   **Backend:** Python with the FastAPI framework.
*   **AI Services:** `openai`, `google-generativeai`
*   **Web Server:** `uvicorn`
*   **Frontend:** Vanilla JavaScript, HTML, and CSS.
*   **Containerization:** Docker

## Setup & Installation

1.  **Prerequisites:** Ensure you have Docker installed on your system.
2.  **Clone the Repository:**
    ```bash
    git clone https://github.com/your-username/AI-Room-Cleaner.git
    cd AI-Room-Cleaner
    ```
3.  **Configuration:** The application is configured via environment variables. These can be set in a `.env` file or directly in the Home Assistant addon configuration.
    *   `CAMERA_ENTITY_ID`: The entity ID of the camera in Home Assistant.
    *   `OPENAI_API_KEY`: Your API key for the OpenAI or Google AI service.
    *   `AI_MODEL`: The specific AI model to use (e.g., `gpt-4`, `gemini-pro`).
    *   `UPDATE_FREQUENCY`: How often the analysis should run automatically.
    *   `PROMPT`: The custom prompt to send to the AI model for analysis.
4.  **Build the Docker Image:**
    ```bash
    docker build -t ai-room-cleaner .
    ```

## How to Run

### As a Standalone Docker Container:

1.  **Run the container**, passing in the required environment variables:
    ```bash
    docker run -d -p 8000:8000 \
      --name ai-room-cleaner \
      -e CAMERA_ENTITY_ID="your_camera_entity" \
      -e OPENAI_API_KEY="your_api_key" \
      -e AI_MODEL="your_ai_model" \
      -e UPDATE_FREQUENCY="60" \
      -e PROMPT="Analyze this room for messes." \
      ai-room-cleaner
    ```
2.  **Access the application** by navigating to `http://localhost:8000` in your web browser.

### As a Home Assistant Addon:

1.  Add the project repository to your Home Assistant instance.
2.  Install the "AI Room Cleaner" addon from the addon store.
3.  Configure the addon with your camera entity, API key, and other settings in the "Configuration" tab.
4.  Start the addon.
5.  Access the web UI through the sidebar link or by visiting the appropriate URL.