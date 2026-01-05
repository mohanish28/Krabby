from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import ollama
import requests
# import google.generativeai as genai  # Deprecated - use google.genai instead if needed
from groq import Groq
from together import Together
import cohere
import os

class BaseModel(ABC):
    """Base class for all LLM models"""
    
    def __init__(self, name: str, **kwargs):
        self.name = name
    
    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = None) -> str:
        pass

class OllamaModel(BaseModel):
    """Wrapper for Ollama models (free, local)"""
    
    def __init__(self, name: str, base_url: str = "http://localhost:11434", **kwargs):
        super().__init__(name)
        self.base_url = base_url
        try:
            self.client = ollama.Client(host=base_url)
            # Test connection by listing models
            self.client.list()
        except Exception as e:
            raise Exception(f"Cannot connect to Ollama at {base_url}. Make sure Ollama is running. Error: {str(e)}")
    
    def generate(self, prompt: str, system_prompt: str = None) -> str:
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Try with the exact name first
            try:
                response = self.client.chat(
                    model=self.name,
                    messages=messages,
                    options={
                        "temperature": 0.7,
                        "num_predict": 1024
                    }
                )
                return response['message']['content']
            except Exception as e:
                # If exact name fails, try with :latest tag
                if ":latest" not in self.name:
                    try:
                        response = self.client.chat(
                            model=f"{self.name}:latest",
                            messages=messages,
                            options={
                                "temperature": 0.7,
                                "num_predict": 1024
                            }
                        )
                        return response['message']['content']
                    except:
                        pass
                raise e
        except Exception as e:
            raise Exception(f"Error generating response from Ollama {self.name}: {str(e)}. Make sure the model is installed: ollama pull {self.name}")

class GroqModel(BaseModel):
    """Wrapper for Groq API (Free, Very Fast)"""
    
    def __init__(self, name: str, api_key: str, **kwargs):
        super().__init__(name)
        if not api_key:
            raise ValueError("Groq API key is required")
        self.client = Groq(api_key=api_key)
    
    def generate(self, prompt: str, system_prompt: str = None) -> str:
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.name,
                messages=messages,
                temperature=0.7,
                max_tokens=1024
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Error generating response from Groq {self.name}: {str(e)}")

class HuggingFaceModel(BaseModel):
    """Wrapper for Hugging Face Inference API (Free)"""
    
    def __init__(self, name: str, api_key: str = "", **kwargs):
        super().__init__(name)
        self.api_key = api_key
        self.api_url = f"https://api-inference.huggingface.co/models/{name}"
    
    def generate(self, prompt: str, system_prompt: str = None) -> str:
        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            payload = {
                "inputs": full_prompt,
                "parameters": {
                    "max_new_tokens": 512,
                    "temperature": 0.7,
                    "return_full_text": False
                }
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get("generated_text", str(result[0]))
            return str(result)
        except Exception as e:
            raise Exception(f"Error generating response from HuggingFace {self.name}: {str(e)}")

class GoogleModel(BaseModel):
    """Wrapper for Google Gemini API (Free) - DEPRECATED"""
    
    def __init__(self, name: str, api_key: str, **kwargs):
        super().__init__(name)
        raise NotImplementedError(
            "Google Gemini support is deprecated. The google.generativeai package is no longer maintained. "
            "Please use google.genai instead or use other model providers."
        )
        # if not api_key:
        #     raise ValueError("Google API key is required")
        # genai.configure(api_key=api_key)
        # Store API key and model name separately
        self.api_key = api_key
        self.model_name = name
        # Map model names to correct API names
        self.model_name_map = {
            "gemini-1.5-flash": "gemini-1.5-flash-latest",
            "gemini-1.5-pro": "gemini-1.5-pro-latest",
            "gemini-pro": "gemini-pro"
        }
    
    def generate(self, prompt: str, system_prompt: str = None) -> str:
        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # Try the mapped name first, then fallback to original name
            api_model_name = self.model_name_map.get(self.model_name, self.model_name)
            
            # Create model instance fresh each time
            model = genai.GenerativeModel(api_model_name)
            
            try:
                response = model.generate_content(
                    full_prompt,
                    generation_config={
                        "temperature": 0.7,
                        "max_output_tokens": 1024
                    }
                )
                return response.text
            except Exception as e:
                # If mapped name fails, try original name
                if api_model_name != self.model_name:
                    model = genai.GenerativeModel(self.model_name)
                    response = model.generate_content(
                        full_prompt,
                        generation_config={
                            "temperature": 0.7,
                            "max_output_tokens": 1024
                        }
                    )
                    return response.text
                else:
                    raise e
        except Exception as e:
            raise Exception(f"Error generating response from Google {self.name}: {str(e)}")

class TogetherModel(BaseModel):
    """Wrapper for Together AI (Free Tier)"""
    
    def __init__(self, name: str, api_key: str, **kwargs):
        super().__init__(name)
        if not api_key:
            raise ValueError("Together API key is required")
        self.client = Together(api_key=api_key)
    
    def generate(self, prompt: str, system_prompt: str = None) -> str:
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.name,
                messages=messages,
                temperature=0.7,
                max_tokens=1024
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Error generating response from Together {self.name}: {str(e)}")

class CohereModel(BaseModel):
    """Wrapper for Cohere API (Free Tier)"""
    
    def __init__(self, name: str, api_key: str, **kwargs):
        super().__init__(name)
        if not api_key:
            raise ValueError("Cohere API key is required")
        self.client = cohere.Client(api_key=api_key)
    
    def generate(self, prompt: str, system_prompt: str = None) -> str:
        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            response = self.client.generate(
                model=self.name,
                prompt=full_prompt,
                temperature=0.7,
                max_tokens=1024
            )
            return response.generations[0].text
        except Exception as e:
            raise Exception(f"Error generating response from Cohere {self.name}: {str(e)}")

def create_model(model_config: Dict[str, Any]) -> BaseModel:
    """Factory function to create model instances"""
    provider = model_config["provider"]
    name = model_config["name"]
    
    if provider == "ollama":
        base_url = model_config.get("base_url", "http://localhost:11434")
        return OllamaModel(name, base_url=base_url)
    elif provider == "groq":
        api_key = model_config.get("api_key", "")
        return GroqModel(name, api_key=api_key)
    elif provider == "huggingface":
        api_key = model_config.get("api_key", "")
        return HuggingFaceModel(name, api_key=api_key)
    elif provider == "google":
        api_key = model_config.get("api_key", "")
        return GoogleModel(name, api_key=api_key)
    elif provider == "together":
        api_key = model_config.get("api_key", "")
        return TogetherModel(name, api_key=api_key)
    elif provider == "cohere":
        api_key = model_config.get("api_key", "")
        return CohereModel(name, api_key=api_key)
    else:
        raise ValueError(f"Unknown provider: {provider}")

