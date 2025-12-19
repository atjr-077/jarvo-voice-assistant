Jarvo – AI Voice Assistant

Jarvo is a Python-based AI voice assistant that listens to voice commands, responds using text-to-speech, and performs automated tasks. The project is built with a modular architecture and focuses on real-time voice interaction and AI-powered conversations.

Features
Jarvo supports voice command recognition, text-to-speech responses, AI-powered conversational handling, wake-word detection, command execution and automation, JSON-based memory and command history, and optional GUI support.

Tech Stack
The project is built using Python, SpeechRecognition, pyttsx3 for text-to-speech, OpenAI or Gemini APIs for AI interaction, and JSON for lightweight data storage.

Project Structure
The repository includes the main assistant file (Voice_Assistant.py), core modules such as actions.py, ai_conversation.py, speech.py, tts.py, wake_word.py, utils.py, config.py, and gui.py. It also contains assistant_memory.json and command_history.json for storing data, a run_assistant.bat file for Windows users, a README.md file, and a .gitignore file.

How to Run
First, clone the repository from GitHub and navigate into the project directory. Install all required dependencies using pip and the requirements.txt file. Create a .env file using the provided .env.example and add your API keys. Finally, run the assistant using the command python Voice_Assistant.py.

How It Works
Jarvo captures audio input from the microphone and converts speech into text using speech recognition. The processed command is then handled either through predefined logic or AI-based conversation models. Responses are generated and delivered back to the user using text-to-speech. User interactions and command history are stored in JSON files for persistence.

Future Improvements
Planned improvements include better wake-word accuracy, cross-platform support, a more advanced graphical interface, a plugin-based command system, and enhanced long-term memory handling.

Author
Arpit Tiwari

Feel free to star the repository or share feedback.
