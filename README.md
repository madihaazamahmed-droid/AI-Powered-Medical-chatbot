# ai_medical_chatbot
This project, AI-Powered Medical Chatbot, is an intelligent assistant built with Python and AI models to provide basic health-related guidance and information. It is designed for educational purposes only and should never be used as a substitute for professional medical advice. The chatbot offers an interactive interface for medical queries, handles API keys securely through a local .env file, and has a modular codebase that makes it easy to extend or adapt. To get started, clone the repository from GitHub, create a virtual environment, and install the dependencies listed in requirements.txt. You will then need to configure your environment variables by creating a .env file in the project root and adding your Groq API key, which is safely ignored by Git thanks to .gitignore. Once setup is complete, you can run the chatbot with python app.py and begin interacting with it. The project emphasizes security best practices, encouraging developers to keep secrets private, use GitHub Actions secrets or cloud secret managers for deployment, and always verify that .env is excluded from commits. Contributions are welcome, and developers can fork the repository, create feature branches, and submit pull requests to improve functionality. The project is licensed under MIT, making it open for learning and collaboration, and it reflects a commitment to clean repo hygiene, beginner-friendly documentation, and secure coding practices.
1. Clone the Repository
```bash
git clone https://github.com/madihaazamahmed-droid/AI-Powered-Medical-chatbot.git
cd AI-Powered-Medical-chatbot
2. Create a Virtual Environment
python -m venv .venv
source .venv/bin/activate   # On Linux/Mac
.venv\Scripts\activate      # On Windows
3. Install Dependencies
pip install -r requirements.txt
4.Configure Environment Variables
Create a .env file in the project root:
GROQ_API_KEY=your_api_key_here
Do not commit .env to GitHub. It is already ignored via .gitignore.
5. Run the Chatbot
python app.py













