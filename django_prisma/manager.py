from django.db import models

class CacheableManager(models.Manager):
    def __init__(self, swr: int, ttl: int):
        self.swr = swr
        self.ttl = ttl
        super().__init__()

