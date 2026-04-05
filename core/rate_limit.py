from functools import wraps

from django.core.cache import cache
from django.http import JsonResponse


def rate_limited(
    key_prefix: str,
    limit: int,
    window_sec: int,
    cooldown_base_sec: int = 30,
    cooldown_max_sec: int = 600,
):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            identity = str(request.user.id) if request.user.is_authenticated else request.META.get('REMOTE_ADDR', 'anon')
            cache_key = f'rl:{key_prefix}:{identity}'
            block_key = f'rl:block:{key_prefix}:{identity}'
            strike_key = f'rl:strike:{key_prefix}:{identity}'

            blocked_for = cache.get(block_key)
            if blocked_for:
                return JsonResponse(
                    {
                        'ok': False,
                        'error': 'rate_limited',
                        'detail': 'Слишком много запросов. Попробуйте чуть позже.',
                        'retry_after': int(blocked_for),
                    },
                    status=429,
                )

            current = cache.get(cache_key)
            if current is None:
                cache.set(cache_key, 1, timeout=window_sec)
            else:
                if int(current) >= limit:
                    strikes = int(cache.get(strike_key) or 0) + 1
                    cache.set(strike_key, strikes, timeout=max(window_sec * 4, cooldown_max_sec))
                    cooldown = min(cooldown_max_sec, cooldown_base_sec * (2 ** (strikes - 1)))
                    cache.set(block_key, cooldown, timeout=cooldown)
                    return JsonResponse(
                        {
                            'ok': False,
                            'error': 'rate_limited',
                            'detail': 'Слишком много запросов. Попробуйте чуть позже.',
                            'retry_after': int(cooldown),
                        },
                        status=429,
                    )
                cache.incr(cache_key)
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator
