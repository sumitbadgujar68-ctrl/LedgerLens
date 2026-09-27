import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

async def main():
    engine = create_async_engine(DATABASE_URL)
    tables = [
        'investigators',
        'cases',
        'entities',
        'entity_addresses',
        'transactions',
        'trace_runs',
        'graphs',
        'risk_scores',
        'patterns',
        'vasp_attributions',
        'evidence',
        'reports',
        'jobs'
    ]
    
    print("DATABASE ROW COUNTS:")
    for table in tables:
        try:
            async with engine.connect() as conn:
                result = await conn.execute(text(f"SELECT COUNT(*) FROM {table};"))
                count = result.scalar()
                print(f"- {table}: {count}")
        except Exception as e:
            print(f"- {table}: Error ({str(e).strip()})")

    try:
        async with engine.connect() as conn:
            res = await conn.execute(text("SELECT blockchain, count(*) FROM cases GROUP BY blockchain;"))
            print("\nCASES BY BLOCKCHAIN:")
            for row in res.fetchall():
                print(f"- {row[0]}: {row[1]}")
    except Exception as e:
        print(f"Error querying cases by blockchain: {e}")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
