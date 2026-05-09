from openai import OpenAI
from django.conf import settings


class DeepSeekClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._client = OpenAI(
                base_url="https://integrate.api.nvidia.com/v1",
                api_key=settings.NVIDIA_API_KEY,
            )
        return cls._instance

    @property
    def client(self):
        return self._client

    def chat(self, message: str, stream: bool = True):
        return self.client.chat.completions.create(
            model=settings.DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": message}],
            temperature=1,
            top_p=0.95,
            max_tokens=16384,
            extra_body={"chat_template_kwargs": {"thinking": False}},
            stream=stream,
        )


def stream_chat(message: str):
    client = DeepSeekClient()
    completion = client.chat(message, stream=True)
    for chunk in completion:
        if not getattr(chunk, "choices", None):
            continue
        if chunk.choices and chunk.choices[0].delta.content is not None:
            yield chunk.choices[0].delta.content