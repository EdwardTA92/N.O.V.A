class _ChatCompletions:
    async def create(self, *args, **kwargs):
        raise NotImplementedError("OpenRouter SDK not implemented")

class _Chat:
    def __init__(self):
        self.completions = _ChatCompletions()

class OpenRouter:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.chat = _Chat()
