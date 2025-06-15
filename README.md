# AI Room Cleaner

## Description

AI Room Cleaner is a smart home application designed to analyze the cleanliness of a room using artificial intelligence. It captures an image from a designated camera, sends it to a powerful AI model (either OpenAI's GPT or Google's Gemini), and receives a list of "messes" or cleaning tasks. These tasks are then displayed on a simple, intuitive web interface, helping you identify what needs cleaning. The entire application is containerized with Docker, making it easy to set up and run.

## Features

*   **AI-Powered Mess Detection:** Leverages generative AI to analyze room images and identify areas that require cleaning.
*   **Dual AI Model Support:** Supports both OpenAI and Google Generative AI models for flexibility.
*   **Web-Based Interface:** A clean and simple frontend allows users to trigger room analysis and view a list of cleaning tasks.
*   **Camera Integration:** Connects to a camera entity to fetch real-time images for analysis.
*   **Task List Generation:** Automatically generates a to-do list based on the AI's findings.
*   **Cleanliness Score:** Calculates and displays a "cleanliness score" to quickly gauge the room's state.
*   **Dockerized Deployment:** Comes with a `Dockerfile` and `docker-compose.yml` for easy, consistent deployment.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

*   [Python 3.9+](https://www.python.org/)
*   [Node.js](https://nodejs.org/) (which includes npm)
*   [Docker](https://www.docker.com/get-started)
*   [Poetry](https://python-poetry.org/docs/#installation) for Python dependency management.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/AI-Room-Cleaner.git
    cd AI-Room-Cleaner
    ```

2.  **Backend Setup:**
    ```bash
    # Navigate to the backend directory
    cd ai_room_cleaner/backend

    # Install Python dependencies using Poetry
    poetry install
    ```

3.  **Frontend Setup:**
    ```bash
    # Navigate to the frontend directory
    cd ai_room_cleaner/frontend

    # Install JavaScript dependencies
    npm install
    ```

4.  **Configuration:**
    The application is configured via environment variables. You can create a `.env` file in the root of the `ai_room_cleaner` directory or set them in your environment.

    ```
    CAMERA_ENTITY_ID="your_camera_entity"
    OPENAI_API_KEY="your_api_key"
    AI_MODEL="your_ai_model"
    # Example: gpt-4, gemini-1.5-pro-latest
    ```

### Running the Application

**With Docker (Recommended):**

1.  **Build and run the containers:**
    ```bash
    docker-compose up --build
    ```

2.  The application will be available at `http://localhost:8000`.

**Locally for Development:**

1.  **Start the backend server:**
    From the `ai_room_cleaner/backend` directory:
    ```bash
    poetry run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    ```

2.  **Start the frontend development server:**
    From the `ai_room_cleaner/frontend` directory:
    ```bash
    npm run dev
    ```
    The frontend will be available at the URL provided by Vite (usually `http://localhost:5173`).

## Usage

Once the application is running, open your web browser and navigate to the appropriate URL (`http://localhost:8000` if using Docker, or the Vite dev server URL).

1.  Click the "Analyze Room" button.
2.  The application will capture an image, send it to the configured AI service, and display the results.
3.  You will see a list of messes, a cleanliness score, and the image that was analyzed.

## Project Structure

The project is organized into two main parts: a Python backend and a JavaScript frontend.

```
AI-Room-Cleaner/
├── ai_room_cleaner/
│   ├── backend/        # FastAPI application
│   │   ├── api/        # API endpoints
│   │   ├── core/       # Core components (config, state)
│   │   ├── services/   # Business logic (AI, camera)
│   │   ├── tests/      # Backend tests
│   │   └── main.py     # Application entry point
│   ├── frontend/       # Vanilla JS frontend
│   │   ├── modules/    # JavaScript modules (api, ui, etc.)
│   │   ├── index.html  # Main HTML file
│   │   ├── style.css   # Styles
│   │   └── main.js     # Main JS entry point
│   └── data/           # Data files (e.g., images)
├── docker-compose.yml  # Docker Compose configuration
├── Dockerfile          # Dockerfile for the application
└── README.md           # This file
```

## Technologies Used

*   **Backend:**
    *   [Python](https://www.python.org/)
    *   [FastAPI](https://fastapi.tiangolo.com/)
    *   [Uvicorn](https://www.uvicorn.org/)
    *   [Poetry](https://python-poetry.org/)
    *   [OpenAI Python Library](https://github.com/openai/openai-python)
    *   [Google Generative AI](https://github.com/google/generative-ai-python)

*   **Frontend:**
    *   Vanilla [JavaScript](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
    *   [Vite](https://vitejs.dev/)
    *   HTML5 & CSS3

*   **Containerization:**
    *   [Docker](https://www.docker.com/)