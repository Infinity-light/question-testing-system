import os
import time
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from flask import current_app


class HunyuanService:
    """Service for interacting with Hunyuan AI API"""

    def __init__(self):
        self.client = None
        self.model = None

    def initialize(self):
        """Initialize OpenAI client with Hunyuan configuration"""
        api_key = current_app.config['HUNYUAN_API_KEY']
        base_url = current_app.config['HUNYUAN_BASE_URL']
        self.model = current_app.config['HUNYUAN_MODEL']

        if not api_key:
            raise ValueError("HUNYUAN_API_KEY not configured")

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def call_hunyuan_stateless(self, question: str) -> str:
        """
        Make a stateless API call to Hunyuan AI.
        Each call is independent with no conversation history.

        Args:
            question: The question text to send to the AI

        Returns:
            The AI's response as a string
        """
        if not self.client:
            self.initialize()

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": question}],
                temperature=0.7  # Use temperature > 0 for varied responses
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            current_app.logger.error(f"Hunyuan API call failed: {str(e)}")
            raise

    def verify_answer(self, ai_answer: str, standard_answer: str, question: str) -> tuple[bool, str]:
        """
        Verify if the AI's answer matches the standard answer using Hunyuan.

        Args:
            ai_answer: The answer provided by the AI
            standard_answer: The correct standard answer
            question: The original question text

        Returns:
            Tuple of (is_correct: bool, verification_response: str)
        """
        prompt = f"""请判断以下两个答案是否一致：

问题：{question}

标准答案：{standard_answer}

AI回答：{ai_answer}

请只回答"一致"或"不一致"。"""

        try:
            verification_response = self.call_hunyuan_stateless(prompt)
            is_correct = "一致" in verification_response.lower()
            return is_correct, verification_response
        except Exception as e:
            current_app.logger.error(f"Answer verification failed: {str(e)}")
            return False, f"Verification error: {str(e)}"

    def add_rate_limit_delay(self):
        """Add delay between API calls for rate limiting"""
        time.sleep(0.5)


# Global service instance
hunyuan_service = HunyuanService()
