import requests
import os
from openai import OpenAI
from typing import Dict, Any, Literal, Optional
from config import Config
import google.generativeai as genai
import anthropic


class LLMConfigs:
    """Configuration class for LLM API settings."""

    def __init__(self):
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
        self.anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')
        self.google_api_key = os.environ.get('GEMINI_API_KEY')
        self.api_timeout = getattr(Config, 'API_TIMEOUT', 30)

        # API endpoints
        self.openai_url = "https://api.openai.com/v1/chat/completions"
        self.anthropic_url = "https://api.anthropic.com/v1/messages"
        self.google_url = "https://generativelanguage.googleapis.com/v1beta/models"


ClaudeModel = Literal[
    "claude-opus-4-1-20250805",
    "claude-opus-4-1",   # alias
    "claude-opus-4-20250514",
    "claude-opus-4-0",   # alias
    "claude-sonnet-4-20250514",
    "claude-sonnet-4-0",  # alias
    "claude-3-7-sonnet-20250219",
    "claude-3-7-sonnet-latest",  # alias
    "claude-3-5-haiku-20241022",
    "claude-3-5-haiku-latest",   # alias
    "claude-3-5-sonnet-latest",    # alias
    "claude-3-opus-latest",       # alias
    "claude-3-haiku-20240307",
]


class LLMModels:
    """Class to interact with various LLM APIs."""

    def __init__(self):
        self.config = LLMConfigs()
        self.openai_client = OpenAI(api_key=self.config.openai_api_key)

    def call_openai(self, prompt: str, system_prompt: str = "", model: Literal["gpt-5", "gpt-5-mini", "gpt-5-nano", "gpt-4.1"] = "gpt-5-mini") -> Optional[str]:
        """Call OpenAI API."""
        if not self.config.openai_api_key:
            raise ValueError("OpenAI API key not configured")

        try:
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
            )

            return response.choices[0].message.content
        except requests.RequestException as e:
            print(f"Error calling OpenAI API: {e}")
            return None

    def call_anthropic(self, prompt: str, system_prompt: str = "",  model: ClaudeModel = "claude-opus-4-1-20250805", max_tokens: int = 1000) -> Optional[str]:
        """Call Anthropic Claude API."""
        if not self.config.anthropic_api_key:
            raise ValueError("Anthropic API key not configured")
        try:
            client = anthropic.Anthropic(
                api_key=self.config.anthropic_api_key,
            )
            message = client.messages.create(
                model=model,
                max_tokens=1024,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": prompt},
                ]
            )
            return message.content
        except requests.RequestException as e:
            print(f"Error calling Anthropic API: {e}")
            return None

    def call_google(self, prompt: str, system_prompt: str = "", model: str = "gemini-2.5-flash") -> Optional[str]:
        """Call Google Gemini API."""
        if not self.config.google_api_key:
            raise ValueError("Google API key not configured")

        try:
            client = genai.Client(
                api_key=self.config.google_api_key
            )

            response = client.models.generate_content(
                model=model, contents=prompt
            )
            return response.text
        except requests.RequestException as e:
            print(f"Error calling Google API: {e}")
            return None

    def generate_response(self, prompt: str, provider: str = "openai", **kwargs) -> Optional[str]:
        """Generate response from specified LLM provider."""
        if provider.lower() == "openai":
            return self.call_openai(prompt, **kwargs)
        elif provider.lower() == "anthropic":
            return self.call_anthropic(prompt, **kwargs)
        elif provider.lower() == "google":
            return self.call_google(prompt, **kwargs)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
