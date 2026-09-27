import asyncio
import sys
sys.path.insert(0, 'backend')
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check_evidence():
    engine = create_async_engine('postgresql+asyncpg://postgres.masqstgbhzuxhfopmdil:Sumit%4068%23supabase@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres?ssl=require')
    async with engine.begin() as conn:
        # Check evidence for a demo case
        result = await conn.execute(text("SELECT * FROM evidence WHERE case_id = '15087eaa-88a7-4554-8c7e-7112973137bb'"))
        for row in result:
            print(f'Evidence: {row}')
        
        # Also check CASE-2026-000001 specifically
        result = await conn.execute(text("SELECT * FROM evidence WHERE case_id = '8f667699-7f59-4293-8237-15352e34c70b'"))
        for row in result:
            print(f'CASE-2026-000001 Evidence: {row}')

asyncio.run(check_evidence())