import asyncio
import os

from google import genai
from google.genai import errors


class GeminiAffectiveClient:
    """Asynchronous client for interacting with Google Gemini API to analyze
    affective contexts using the modern google-genai SDK.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "gemini-flash-lite-latest",
    ):
        # A nova biblioteca utiliza o genai.Client()
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model_name = model_name

        # O cliente herda automaticamente a GEMINI_API_KEY do ambiente,
        # mas passamos explicitamente se fornecido
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = genai.Client()

    async def invoke_prompt(self, prompt: str, timeout_seconds: float = 8.0) -> str:
        """Invokes the Gemini model asynchronously to generate text content.
        Wraps the call in a timeout block to prevent network stalling on the
        local system.
        """
        # Fallback defensivo se a chave não estiver no ambiente
        if not self.api_key and not os.getenv("GEMINI_API_KEY"):
            return (
                "[Fallback] GEMINI_API_KEY is not configured. "
                "Affective inference bypassed."
            )

        # Atualização em tempo real caso a variável de ambiente
        # tenha sido injetada após o init
        if not self.api_key and os.getenv("GEMINI_API_KEY"):
            self.api_key = os.getenv("GEMINI_API_KEY", "")
            self.client = genai.Client(api_key=self.api_key)

        try:
            # Proteção estrita de timeout (asyncio 3.11+)
            async with asyncio.timeout(timeout_seconds):
                response = await self.client.aio.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                )
                return response.text

        except TimeoutError:
            return (
                f"[Fallback] Affective inference request timed out after "
                f"{timeout_seconds} seconds."
            )
        except errors.APIError as e:
            return f"[Fallback] Google Cloud API error occurred: {str(e)}"
        except Exception as e:
            return f"[Fallback] Network connection or generic error: {str(e)}"
