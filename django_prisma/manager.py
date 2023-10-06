import dataclasses
from django.db import models

@dataclasses.dataclass
class CacheStrategy:
    ttl: int
    swr: int

class CacheableManager(models.Manager):
    def __init__(self):
        self.cache_strategy = None
        super().__init__()

    def get_queryset(self):
        self.cache_strategy = None
        return super().get_queryset()

    def with_cache(self, cache_strategy: CacheStrategy):
        self.cache_strategy = cache_strategy
        return super().get_queryset()
