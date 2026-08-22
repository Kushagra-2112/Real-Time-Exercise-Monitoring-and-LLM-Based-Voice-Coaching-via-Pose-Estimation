import re
from services.config.workout_config import PROMPT


class LLMCoach:
    def __init__(self, groq_client):
        self.client = groq_client
        self.history = []
        self.system_prompt = PROMPT
        self.model = "qwen/qwen3.6-27b"

    def _clean_output(self, text: str) -> str:
        if not text:
            return ""
        # Strip the model's <think>...</think> reasoning block entirely,
        # keeping only the real final answer that comes after it.
        cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        # Safety net: if the closing tag is missing/truncated mid-stream,
        # cut everything from the opening tag onward.
        if "<think>" in cleaned:
            cleaned = cleaned.split("<think>")[0]
        return cleaned.strip(' "\'\n\r')

    def give_feedback(self, event, exercise=None, issue=None):
        prompt = f"Event: {event}"
        if exercise:
            prompt += f" Exercise: {exercise}"
        if issue:
            prompt += f" Form Issue: {issue}"

        messages = [
            {"role": "system", "content": self.system_prompt},
            *self.history[-10:],
            {"role": "user", "content": prompt}
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.4,
            )
            raw = response.choices[0].message.content or ""
            text = self._clean_output(raw)

            if not text:
                text = "Let's get moving — you've got this!"

            self.history.append({"role": "assistant", "content": text})
            return text
        except Exception as e:
            print(f"[LLM Error] {e}")
            return "Keep steady control throughout the repetition!"