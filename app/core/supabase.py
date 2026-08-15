from functools import lru_cache
from typing import Optional
import logging
from supabase import create_client, Client
from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


@lru_cache()
def get_supabase_client(settings: Optional[Settings] = None) -> Optional[Client]:
    """
    Returns a configured Supabase Client instance.
    Returns None if SUPABASE_URL or SUPABASE_KEY are not configured.
    """
    settings = settings or get_settings()

    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        logger.warning("Supabase URL or Key not set in environment.")
        return None

    try:
        client: Client = create_client(
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_KEY,
        )
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        return None
