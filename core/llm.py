"""
LLM translation support for lazyi18n.
Supports OpenAI-compatible APIs.
"""

import json
from typing import Dict, Optional, List, Callable
from openai import OpenAI


class LLMTranslationError(Exception):
    """Raised when LLM translation fails."""

    pass


class LLMTranslator:
    """Handles translation using OpenAI-compatible LLMs."""

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
    ):
        """
        Initialize LLM translator.

        Args:
            api_key: API key for the LLM service
            base_url: Base URL for the API (optional, defaults to OpenAI)
            model: Model to use (default: gpt-3.5-turbo)
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def translate_key(
        self,
        key: str,
        source_text: str,
        source_locale: str,
        target_locales: List[str],
        log_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, str]:
        """
        Translate a single key to multiple target locales using LLM.

        Args:
            key: The translation key (context)
            source_text: The text to translate
            source_locale: The source language
            target_locales: List of target languages
            log_callback: Optional callback for logging progress

        Returns:
            Dictionary mapping locale -> translated text
        """
        def log(msg: str):
            if log_callback:
                log_callback(msg)

        if not target_locales:
            log("[yellow]No target locales specified.[/]")
            return {}

        log(f"Preparing translation for key: [bold]{key}[/]")
        log(f"Source ({source_locale}): {source_text}")
        log(f"Targets: {', '.join(target_locales)}")
        log(f"Model: {self.model}")

        system_prompt = (
            "You are a professional translator for a software application. "
            "You will receive a JSON object containing the source text, source locale, "
            "target locales, and the translation key (for context). "
            "You must return a JSON object where keys are the target locales and values are the translations. "
            "Do not include any markdown formatting or explanations. Return ONLY raw JSON."
        )

        user_content = {
            "key": key,
            "source_locale": source_locale,
            "source_text": source_text,
            "target_locales": target_locales,
        }

        log("Sending request to LLM API...")
        # log(f"System Prompt: {system_prompt}") # Too verbose? Maybe.
        log(f"User Content: {json.dumps(user_content, indent=2)}")

        try:
            # Check if model is o1-mini or o1-preview which don't support response_format
            is_o1 = self.model.startswith("o1-")
            kwargs = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(user_content)},
                ],
            }
            
            # Only add response_format for non-o1 models and non-claude models (if using via OpenAI compat)
            # Claude models via some proxies might not support json_object type or require different handling
            # But the error specifically said "Input should be 'json_schema'" which suggests a newer OpenAI client validation
            # or a specific model requirement.
            # However, for broad compatibility, we'll try to be safer.
            
            # If the error is "response_format.type: Input should be 'json_schema'", it means the model/client 
            # expects structured outputs (json_schema) instead of json_object, OR the library version is enforcing it.
            # But standard gpt-3.5/4 supports json_object.
            # The traceback shows 'claude-sonnet-4-5' as the model. 
            # If the user is using an OpenAI-compatible endpoint (like Anthropic via a proxy or similar), 
            # it might not support response_format={"type": "json_object"}.
            
            # Let's try to detect if we should omit response_format based on the error, 
            # but we can't easily do that in a single try/catch block without retry logic.
            # For now, let's make response_format optional if it fails, or just rely on the prompt.
            
            # Actually, the safest bet for "OpenAI Compatible" generic usage is to NOT enforce response_format
            # unless we know the model supports it, OR to catch the specific error and retry without it.
            
            try:
                if not is_o1:
                    kwargs["response_format"] = {"type": "json_object"}
                
                log("Attempting request with response_format={'type': 'json_object'}...")
                response = self.client.chat.completions.create(**kwargs)
            except Exception as e:
                # If it fails with a BadRequest related to response_format, try again without it
                if "response_format" in str(e) and "json_object" in kwargs.get("response_format", {}).get("type", ""):
                    log(f"[yellow]Request failed with response_format error: {e}[/]")
                    log("Retrying without response_format...")
                    del kwargs["response_format"]
                    response = self.client.chat.completions.create(**kwargs)
                else:
                    raise e

            log("[green]Response received![/]")
            if hasattr(response, 'usage') and response.usage:
                log(f"Usage: {response.usage.total_tokens} tokens (Prompt: {response.usage.prompt_tokens}, Completion: {response.usage.completion_tokens})")

            content = response.choices[0].message.content
            log(f"Raw content: {content}")

            if not content:
                raise LLMTranslationError("Empty response from LLM")

            # Clean up markdown code blocks if present
            # Some LLMs return markdown code blocks even when asked for raw JSON
            cleaned_content = content
            if "```" in cleaned_content:
                lines = cleaned_content.splitlines()
                cleaned_lines = [line for line in lines if not line.strip().startswith("```")]
                cleaned_content = "\n".join(cleaned_lines)

            translations = json.loads(cleaned_content)
            
            # Validate response contains expected locales
            result = {}
            for locale in target_locales:
                if locale in translations:
                    result[locale] = str(translations[locale])
                else:
                    log(f"[red]Missing translation for locale: {locale}[/]")
            
            return result

        except Exception as e:
            log(f"[bold red]Error during translation: {e}[/]")
            raise LLMTranslationError(f"LLM translation failed: {e}")
