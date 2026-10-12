"""Shared ingest helpers — idempotent insert used by grid and solar."""

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession


async def insert_idempotent(session: AsyncSession, model, rows: list[dict]) -> dict:
    """Insert rows, silently skipping duplicate primary keys (bridge retries,
    duplicates within one request). Returns received/accepted/duplicates."""
    stmt = (
        pg_insert(model)
        .values(rows)
        .on_conflict_do_nothing(index_elements=[model.time])
        .returning(model.time)
    )
    result = await session.execute(stmt)
    accepted = len(result.all())
    await session.commit()
    received = len(rows)
    return {"received": received, "accepted": accepted, "duplicates": received - accepted}
