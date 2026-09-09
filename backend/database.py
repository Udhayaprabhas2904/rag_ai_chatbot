import asyncpg

from backend.config import settings



# DATABASE CONNECTION POOL


_pool: asyncpg.Pool | None = None



# CREATE DATABASE CONNECTION POOL


async def create_pool() -> asyncpg.Pool:

    global _pool

    # If the pool already exists, reuse it.
    if _pool is not None:

        return _pool

    print("Connecting to PostgreSQL...")

    _pool = await asyncpg.create_pool(

        host=settings.POSTGRES_HOST,

        port=settings.POSTGRES_PORT,

        database=settings.POSTGRES_DB,

        user=settings.POSTGRES_USER,

        password=settings.POSTGRES_PASSWORD,

        # Connection pool settings
        min_size=2,

        max_size=10,

        # Connection timeout
        timeout=10,

    )

    print("PostgreSQL connection pool created.")

    return _pool



# GET DATABASE CONNECTION POOL


def get_pool() -> asyncpg.Pool:

    if _pool is None:

        raise RuntimeError(
            "Database pool has not been initialized. "
            "Make sure create_pool() runs during application startup."
        )

    return _pool



# CLOSE DATABASE CONNECTION POOL


async def close_pool() -> None:

    global _pool

    if _pool is None:

        return

    print("Closing PostgreSQL connection pool...")

    await _pool.close()

    _pool = None

    print("PostgreSQL connection pool closed.")