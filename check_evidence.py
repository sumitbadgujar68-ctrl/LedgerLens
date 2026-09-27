import asyncio
import sys
sys.path.insert(0, 'backend')
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check_evidence():
    engine = create_async_engine('postgresql+asyncpg://postgres.masqstgbhzuxhfopmdil:Sumit%4068%23supabase@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres?ssl=require')
    async with engine.begin() as conn:
        # Check evidence for CASE-2026-000001
        result = await conn.execute(text("SELECT * FROM evidence WHERE case_id = '8f667699-7f59-4293-8237-15352e34c70b'"))
        for row in result:
            print(f'Evidence: {row}')
        
        # Check evidence for all cases
        result = await conn.execute(text("SELECT case_id, COUNT(*) as cnt FROM evidence GROUP BY case_id"))
        for row in result:
            print(f'Case {row[0]}: {row[1]} evidence records')

asyncio.run(check_evidence())