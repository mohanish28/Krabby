import os
from dotenv import load_dotenv

load_dotenv()

# Free API Keys (set these in .env file)
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY", "")
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")

# Council settings with environment variable support
DISCUSSION_ROUNDS = int(os.getenv("COUNCIL_DISCUSSION_ROUNDS", "2"))
VOTING_MODE = os.getenv("COUNCIL_VOTING_MODE", "majority")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Model timeout settings
MODEL_TIMEOUT = int(os.getenv("MODEL_TIMEOUT", "60"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

# Model configurations - Mix of Ollama (local) and Free APIs
MODELS = [
    # Ollama Models (Local, Free, No API key needed)
    {
        "name": "qwen3-coder:30b",
        "provider": "ollama"
    },
    {
        "name": "deepseek-r1:8b",
        "provider": "ollama"
    },
    {
        "name": "llama3:latest",
        "provider": "ollama"
    },
    {
        "name": "mistral:latest",
        "provider": "ollama"
    },
    {
        "name": "gemma3:4b",
        "provider": "ollama"
    },
    
    # Groq Models (Free API, Very Fast)
    {
        "name": "llama-3.1-8b-instant",
        "provider": "groq",
        "api_key": GROQ_API_KEY
    },
    {
        "name": "llama-3.3-70b-versatile",
        "provider": "groq",
        "api_key": GROQ_API_KEY
    },
    
    # Google Gemini - REMOVED: API version issues (404 errors)
    # If you want to use Gemini, you may need to update the API library
    # {
    #     "name": "gemini-pro",
    #     "provider": "google",
    #     "api_key": GOOGLE_API_KEY
    # },
    
    # Together AI (Free Tier) - Optional
    {
        "name": "meta-llama/Llama-3-8b-chat-hf",
        "provider": "together",
        "api_key": TOGETHER_API_KEY
    },
    
    # Cohere (Free Tier) - Optional
    {
        "name": "command",
        "provider": "cohere",
        "api_key": COHERE_API_KEY
    }
]

# Note: DISCUSSION_ROUNDS, VOTING_MODE, and OLLAMA_BASE_URL are now defined above
# They can be overridden via environment variables (see env.example)

