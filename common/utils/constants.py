# utils/constants.py
import asyncpg


async def get_constant(pool, key: str, default=None, cast_type: str = "str"):
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT value, type FROM app_constants WHERE key = $1", key
        )
        if not row:
            return default

        val, typ = row["value"], row["type"]

        if typ == "int":
            return int(val)
        if typ == "float":
            return float(val)
        if typ == "bool":
            return val.lower() in ("true", "1", "yes")
        return val
