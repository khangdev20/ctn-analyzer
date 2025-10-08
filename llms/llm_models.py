import requests
import os
import logging
from openai import OpenAI
from typing import Dict, Any, Literal, Optional
from config.config import Config
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
        self.logger = logging.getLogger(__name__)

    def call_openai(self, prompt: str, system_prompt: str = "",
                    model: Literal["gpt-5", "gpt-5-mini",
                                   "gpt-5-nano", "gpt-4.1"] = "gpt-5-mini",
                    max_tokens=1000,
                    temperature=0.7,
                    context: str = "general") -> Optional[str]:
        """Call OpenAI API with context tracking."""
        if not self.config.openai_api_key:
            raise ValueError("OpenAI API key not configured")

        # Log the request with context
        self.logger.info(
            f"[LLM_REQUEST] OpenAI {model} - Context: {context} - Tokens: {max_tokens}")

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

            # Log successful response
            response_text = response.choices[0].message.content
            self.logger.info(
                f"[LLM_SUCCESS] OpenAI {model} - Context: {context} - Response length: {len(response_text) if response_text else 0} chars")
            return response_text
        except Exception as e:
            self.logger.error(
                f"[LLM_ERROR] OpenAI {model} - Context: {context} - Error: {e}")
            return None

    def call_anthropic(self, prompt: str, system_prompt: str = "",  model: ClaudeModel = "claude-opus-4-1-20250805", max_tokens: int = 1000, context: str = "general") -> Optional[str]:
        """Call Anthropic Claude API with context tracking."""
        if not self.config.anthropic_api_key:
            raise ValueError("Anthropic API key not configured")

        # Log the request with context
        self.logger.info(
            f"[LLM_REQUEST] Anthropic {model} - Context: {context} - Tokens: {max_tokens}")

        try:
            client = anthropic.Anthropic(
                api_key=self.config.anthropic_api_key,
            )
            message = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": prompt},
                ]
            )
            # Handle Anthropic response format (list of content blocks)
            if message.content and len(message.content) > 0:
                response_text = message.content[0].text
                self.logger.info(
                    f"[LLM_SUCCESS] Anthropic {model} - Context: {context} - Response length: {len(response_text)} chars")
                return response_text
            else:
                self.logger.warning(
                    f"[LLM_WARNING] Anthropic {model} - Context: {context} - Empty response")
                return None
        except Exception as e:
            self.logger.error(
                f"[LLM_ERROR] Anthropic {model} - Context: {context} - Error: {e}")
            return None

    def call_google(self, prompt: str, system_prompt: str = "", model: str = "gemini-2.5-flash", context: str = "general") -> Optional[str]:
        """Call Google Gemini API with context tracking."""
        if not self.config.google_api_key:
            raise ValueError("Google API key not configured")

        # Log the request with context
        self.logger.info(f"[LLM_REQUEST] Google {model} - Context: {context}")

        try:
            genai.configure(api_key=self.config.google_api_key)
            model_instance = genai.GenerativeModel(model)

            # Combine system prompt and user prompt if system prompt is provided
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

            response = model_instance.generate_content(full_prompt)
            response_text = response.text
            self.logger.info(
                f"[LLM_SUCCESS] Google {model} - Context: {context} - Response length: {len(response_text) if response_text else 0} chars")
            return response_text
        except Exception as e:
            self.logger.error(
                f"[LLM_ERROR] Google {model} - Context: {context} - Error: {e}")
            return None

    def generate_response(self, prompt: str, provider: str = "openai", context: str = "general", **kwargs) -> Optional[str]:
        """Generate response from specified LLM provider."""
        if provider.lower() == "openai":
            return self.call_openai(prompt, context=context, **kwargs)
        elif provider.lower() == "anthropic":
            return self.call_anthropic(prompt, context=context, **kwargs)
        elif provider.lower() == "google":
            return self.call_google(prompt, context=context, **kwargs)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def generate_response_with_fallback(self, prompt: str, system_prompt: str = "",
                                        primary_provider: str = "openai",
                                        fallback_providers: list = None,
                                        **kwargs) -> Optional[str]:
        """
        Generate response with automatic fallback to other providers if primary fails.

        Args:
            prompt: The user prompt
            system_prompt: System instructions
            primary_provider: First provider to try ("openai", "anthropic", "google")
            fallback_providers: List of providers to try if primary fails
            **kwargs: Additional arguments for the API calls (max_tokens, temperature, etc.)

        Returns:
            Generated response or None if all providers fail

        Example:
            llm = LLMModels()
            response = llm.generate_response_with_fallback(
                prompt="Analyze this trend",
                system_prompt="You are a trend analyst",
                primary_provider="openai",
                fallback_providers=["anthropic", "google"],
                max_tokens=500,
                temperature=0.7
            )
        """
        import logging
        logger = logging.getLogger(__name__)

        if fallback_providers is None:
            fallback_providers = ["anthropic", "google"]

        # Create list of providers to try in order
        providers_to_try = [primary_provider] + \
            [p for p in fallback_providers if p != primary_provider]

        for provider in providers_to_try:
            try:
                print(f"[BOT] Attempting to generate response using {provider}")

                result = None
                if provider.lower() == "openai":
                    # Check if API key is available
                    if not self.config.openai_api_key:
                        print(f"[WARNING]  OpenAI API key not configured, skipping")
                        continue
                    result = self.call_openai(prompt, system_prompt, **kwargs)

                elif provider.lower() == "anthropic":
                    # Check if API key is available
                    if not self.config.anthropic_api_key:
                        print(f"[WARNING]  Anthropic API key not configured, skipping")
                        continue
                    result = self.call_anthropic(
                        prompt, system_prompt, **kwargs)

                elif provider.lower() == "google":
                    # Check if API key is available
                    if not self.config.google_api_key:
                        print(f"[WARNING]  Google API key not configured, skipping")
                        continue
                    result = self.call_google(prompt, system_prompt, **kwargs)

                else:
                    print(f"[WARNING]  Unknown provider: {provider}, skipping")
                    continue

                if result and result.strip():
                    print(
                        f"[OK] Successfully generated response using {provider}")
                    return result
                else:
                    print(
                        f"[ERROR] No response from {provider}, trying next provider")

            except Exception as e:
                print(f"[ERROR] Error with {provider}: {e}")
                # Log specific error types for debugging
                if "rate_limit" in str(e).lower() or "quota" in str(e).lower():
                    print(f"   Rate limit/quota exceeded for {provider}")
                elif "api_key" in str(e).lower() or "authentication" in str(e).lower():
                    print(f"   Authentication error for {provider}")
                elif "timeout" in str(e).lower():
                    print(f"   Timeout error for {provider}")
                continue

        print("[ERROR] All LLM providers failed to generate response")
        return None

    def get_available_providers(self) -> dict:
        """
        Check which LLM providers are available (have API keys configured).

        Returns:
            Dictionary with provider names as keys and availability as boolean values
        """
        return {
            "openai": bool(self.config.openai_api_key),
            "anthropic": bool(self.config.anthropic_api_key),
            "google": bool(self.config.google_api_key)
        }

    def test_providers(self, test_prompt: str = "Hello! Please respond with 'OK' if you can see this.") -> dict:
        """
        Test all available providers with a simple prompt.

        Args:
            test_prompt: Simple prompt to test with

        Returns:
            Dictionary with test results for each provider
        """
        results = {}
        available = self.get_available_providers()

        for provider, is_available in available.items():
            if not is_available:
                results[provider] = {"status": "no_api_key", "response": None}
                continue

            try:
                response = self.generate_response(
                    test_prompt, provider=provider, max_tokens=50)
                if response:
                    results[provider] = {
                        "status": "success", "response": response[:100]}
                else:
                    results[provider] = {
                        "status": "no_response", "response": None}
            except Exception as e:
                results[provider] = {"status": "error", "response": str(e)[
                    :100]}

        return results
