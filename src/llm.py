from fastapi import HTTPException
from openai import OpenAI
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

client = OpenAI()


class OpenAIClient:
    def __init__(self, model, max_tokens=1500, temperature=0):
        """
        Base class that interacts with the OpenAI API.
        Child classes will specify the model when initialized.
        """
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    def create_completion(self, prompt):
        """
        Calls the OpenAI API with the provided prompt and returns the response.
        """
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logging.error(f"OpenAI API error: {e}")
            raise HTTPException(status_code=500, detail="OpenAI API error") from e


class GPT4Client(OpenAIClient):
    def __init__(self, max_tokens=1500, temperature=0):
        """
        GPT-4 specific client that inherits from OpenAIClient.
        """
        super().__init__(model="gpt-4o", max_tokens=max_tokens, temperature=temperature)


class GPT35Client(OpenAIClient):
    def __init__(self, max_tokens=1500, temperature=0):
        """
        GPT-3.5 specific client that inherits from OpenAIClient.
        """
        super().__init__(
            model="gpt-3.5-turbo", max_tokens=max_tokens, temperature=temperature
        )


class GPT4oClient(OpenAIClient):
    def __init__(self, max_tokens=1500, temperature=0):
        """
        GPT-4o specific client that inherits from OpenAIClient.
        """
        super().__init__(model="gpt-4o", max_tokens=max_tokens, temperature=temperature)
