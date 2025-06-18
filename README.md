# AI Room Cleaner - Home Assistant Addon

## Description

AI Room Cleaner is a Home Assistant addon that analyzes the cleanliness of a room using artificial intelligence. It captures an image from a designated camera, sends it to a powerful AI model (either OpenAI's GPT or Google's Gemini), and creates a to-do list of cleaning tasks directly in Home Assistant.

## Features

*   **AI-Powered Mess Detection:** Leverages generative AI to analyze room images and identify areas that require cleaning.
*   **Dual AI Model Support:** Supports both OpenAI and Google Generative AI models for flexibility.
*   **Home Assistant Integration:** Creates and manages a to-do list entity and sensors for cleanliness score and last analysis time.
*   **Camera Integration:** Connects to any Home Assistant camera entity to fetch real-time images for analysis.
*   **Automatic Task Management:** Can be configured to periodically re-analyze the room and automatically mark completed tasks off the to-do list.

## Installation

1.  **Add the Repository:** Add this repository to your Home Assistant instance as a custom addon repository.
2.  **Install the Addon:** Find the "AI Room Cleaner" addon in the addon store and click "Install".
3.  **Configure the Addon:** Before starting the addon, configure the following options:
    *   `camera_entity_id`: The entity ID of the camera to use for analysis.
    *   `ai_provider`: The AI service to use.
    *   `api_key`: Your API key for the selected AI provider.
    *   `recheck_interval_minutes`: How often to re-analyze the room.
    *   `todo_list_name`: The name of the to-do list to create in Home Assistant.

## Usage

Once the addon is running, it will automatically begin analyzing the specified camera image at the configured interval. You can also trigger an analysis manually by calling the `ai_room_cleaner.analyze_room` service.

A new to-do list and sensors will be created in Home Assistant with the names you configured.