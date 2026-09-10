"""PyBreaker circuit initialization.

========================================================================================================================
Name:         src/event_driven/infrastructure/config/init_pybreaker.py
Description:  Initialize the Redis-backed circuit breaker used by infrastructure adapters.
Author:       PyModeller
Status:       Development
Copyright ©2026. All rights reserved.
========================================================================================================================
"""

from functools import lru_cache

import pybreaker
import redis

from .init_settings import get_redis_configuration_settings


@lru_cache(maxsize=1)
def broker_pybreaker() -> pybreaker.CircuitBreaker:
    """Initialize all settings.

    If force_reload is True, clears the lru_cache for each getter.
    """
    # Initialize / Warm up cache
    redis_conf = get_redis_configuration_settings()
    conf_dumps = redis_conf.model_dump()
    if isinstance(redis_conf.db, int):
        conf_dumps["db"] = str(redis_conf.db)
    redis_client = redis.Redis(**conf_dumps)

    return pybreaker.CircuitBreaker(
        fail_max=5,
        reset_timeout=60,
        state_storage=pybreaker.CircuitRedisStorage(
            state=pybreaker.STATE_CLOSED, redis_object=redis_client, namespace="imessage_publish_circuit"
        ),
    )
