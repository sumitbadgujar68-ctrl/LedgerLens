import asyncio
from uuid import UUID
from app.db.database import async_session_maker
from app.services.reporting.generator import ReportGenerator
import json

async def test():
    async with async_session_maker() as db:
        rg = ReportGenerator(db)
        rep = await rg.generate(UUID('8f667699-7f59-4293-8237-15352e34c70b'), 'detailed', 'json')
        for s in rep['sections']:
            print(f"=== {s['key']} ({s['title']}) ===")
            if s['key'] in ['case_information', 'initial_reported_wallet', 'investigation_methodology', 'graph_summary', 'risk_analysis', 'detected_patterns', 'evidence_references']:
                print(json.dumps(s.get('data'), default=str, indent=2)[:400])

if __name__ == '__main__':
    asyncio.run(test())
