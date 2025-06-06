# -*- coding: utf-8 -*-
import requests

class VseGPTClient:
    def __init__(self, api_key, api_url):
        self.api_key = api_key
        self.api_url = api_url.rstrip('/')

    def generate_article(self, topic, prompt=None, image_urls=None):
        if prompt is None:
            raise ValueError('Prompt must be provided from utils.py')
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        data = {
            'model': 'openai/gpt-4.1-mini',
            'messages': [
                {'role': 'user', 'content': prompt}
            ]
        }
        r = requests.post(f'{self.api_url}/chat/completions', json=data, headers=headers)
        r.raise_for_status()
        return r.json()