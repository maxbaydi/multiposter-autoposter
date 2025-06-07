# -*- coding: utf-8 -*-
import requests

class VseGPTClient:
    def __init__(self, api_key, api_url):
        self.api_key = api_key
        self.api_url = api_url.rstrip('/')

    def generate_article(self, topic, prompt=None, image_urls=None, timeout=30):
        """Запрашивает генерацию статьи у сервиса VseGPT."""
        if prompt is None:
            raise ValueError('Prompt must be provided from utils.py')

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }

        data = {
            'model': 'openai/gpt-4.1-mini',
            'messages': [
                {'role': 'user', 'content': prompt},
            ],
        }

        try:
            response = requests.post(
                f'{self.api_url}/chat/completions',
                json=data,
                headers=headers,
                timeout=timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise Exception(f'VseGPT API request failed: {exc}') from exc

        return response.json()
