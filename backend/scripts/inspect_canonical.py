import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

async def check():
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        r = await conn.execute(text("SELECT case_id, case_number, reported_wallet_address, fraud_type, status FROM cases WHERE case_number = 'CASE-2026-000001';"))
        case = r.fetchone()
        print("Canonical Case:", case)
        if not case:
            return
        cid = case[0]
        r = await conn.execute(text(f"SELECT count(*), avg(score) FROM risk_scores WHERE case_id = '{cid}';"))
        print("Risk count & avg:", r.fetchall())
        r = await conn.execute(text(f"SELECT wallet_address, score, risk_category FROM risk_scores WHERE case_id = '{cid}' LIMIT 5;"))
        print("Sample risk scores:", r.fetchall())
        r = await conn.execute(text(f"SELECT count(*) FROM patterns WHERE case_id = '{cid}';"))
        print("Patterns count:", r.scalar())
        r = await conn.execute(text(f"SELECT count(*) FROM evidence WHERE case_id = '{cid}';"))
        print("Evidence count:", r.scalar())
        r = await conn.execute(text(f"SELECT count(*) FROM vasp_attributions WHERE case_id = '{cid}';"))
        print("VASP attributions count:", r.scalar())
        r = await conn.execute(text(f"SELECT count(*) FROM transactions WHERE case_id = '{cid}';"))
        print("Transactions count:", r.scalar())
        r = await conn.execute(text(f"SELECT trace_id, start_wallet_address, status FROM trace_runs WHERE case_id = '{cid}';"))
        print("Trace runs:", r.fetchall())

if __name__ == "__main__":
    asyncio.run(check())
