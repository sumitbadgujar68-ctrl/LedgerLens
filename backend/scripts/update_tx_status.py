import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

async def update_status():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        res = await conn.execute(text("UPDATE transactions SET status = 'success' WHERE block_number IS NOT NULL AND block_number > 0 AND status = 'unknown';"))
        print("Updated rows:", res.rowcount)
    async with engine.connect() as conn:
        r = await conn.execute(text("SELECT status, count(*) FROM transactions GROUP BY status;"))
        print("New status breakdown:", r.fetchall())

if __name__ == "__main__":
    asyncio.run(update_status())
