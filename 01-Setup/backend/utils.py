# utils.py
# Common utility functions shared across modules

import os
import dotenv

def load_env():
    dotenv.load_dotenv()
    return {
        "LLM_PROVIDER": os.getenv("LLM_PROVIDER"),
        "LLM_MODEL": os.getenv("LLM_MODEL"),
        "LLM_API_KEY": os.getenv("LLM_API_KEY"),
    }
