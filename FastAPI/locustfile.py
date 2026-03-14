import random
import string
from locust import HttpUser, task, between


def random_url():
    path = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f'https://example.com/{path}'


class ShortenerUser(HttpUser):
    wait_time = between(0.5, 1.5)

    def on_start(self):
        r = self.client.post(
            '/api/v1/links/shorten',
            json={'original_url': random_url()},
            name='/shorten [on_start]',
        )
        if r.status_code == 200:
            self.my_short_code = r.json().get('short_code')
        else:
            self.my_short_code = None

    @task(weight=3)
    def create_link(self):
        self.client.post(
            '/api/v1/links/shorten',
            json={'original_url': random_url()},
            name='/shorten',
        )

    @task(weight=5)
    def resolve_link(self):
        if not getattr(self, 'my_short_code', None):
            return
        self.client.get(
            f'/api/v1/links/{self.my_short_code}',
            name='GET /links/{short_code}',
            allow_redirects=False,
        )

    @task(weight=2)
    def get_stats(self):
        if not getattr(self, 'my_short_code', None):
            return
        self.client.get(
            f'/api/v1/links/{self.my_short_code}/stats',
            name='/stats [short_code]',
        )


class CreateOnlyUser(HttpUser):
    wait_time = between(0.2, 0.5)

    @task
    def create_link(self):
        self.client.post(
            '/api/v1/links/shorten',
            json={'original_url': random_url()},
            name='/shorten (create-only)',
        )
