from datetime import timedelta as TimeDelta
from typing import Any, Optional

import msgspec

from flask import Flask
from .._utils import total_seconds
from ..defaults import Defaults
from ..base import ServerSideSession, ServerSideSessionInterface
from redis import Redis


class RedisSession(ServerSideSession):
    pass


class RedisSessionInterface(ServerSideSessionInterface):
    """Uses the Redis key-value store as a session storage. (`redis-py` required)

    :param client: A ``redis.Redis`` instance.
    :param key_prefix: A prefix that is added to all Redis store keys.
    :param use_signer: Whether to sign the session id cookie or not.
    :param permanent: Whether to use permanent session or not.
    :param sid_length: The length of the generated session id in bytes.
    :param serialization_format: The serialization format to use for the session data.

    .. versionadded:: 0.7
        The `serialization_format` and `app` parameters were added.

    .. versionadded:: 0.6
        The `sid_length` parameter was added.

    .. versionadded:: 0.2
        The `use_signer` parameter was added.
    """

    session_class = RedisSession
    ttl = True

    def __init__(
        self,
        client: Optional[Redis] = Defaults.SESSION_REDIS,
        key_prefix: str = Defaults.SESSION_KEY_PREFIX,
        use_signer: bool = Defaults.SESSION_USE_SIGNER,
        permanent: bool = Defaults.SESSION_PERMANENT,
        sid_length: int = Defaults.SESSION_SID_LENGTH,
        serialization_format: str = Defaults.SESSION_SERIALIZATION_FORMAT,
    ):
        if client is None:
            client = Redis()
        self.client = client
        super().__init__(
            None, key_prefix, use_signer, permanent, sid_length, serialization_format
        )

    def _retrieve_session_data(self, store_id: str) -> Optional[dict]:
        # Get the saved session (value) from the database
        serialized_session_data = self.client.get(store_id)
        if serialized_session_data:
            return self.serializer.decode(serialized_session_data)
        return None

    def _delete_session(self, store_id: str) -> None:
        self.client.delete(store_id)

    def _upsert_session(
        self, session_lifetime: TimeDelta, session: ServerSideSession, store_id: str
    ) -> None:
        storage_time_to_live = total_seconds(session_lifetime)

        # Serialize the session data
        serialized_session_data = self.serializer.encode(session)

        # Update existing or create new session in the database
        self.client.set(
            name=store_id,
            value=serialized_session_data,
            ex=storage_time_to_live,
        )