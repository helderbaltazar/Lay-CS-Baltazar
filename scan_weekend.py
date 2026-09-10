import asyncio
from datetime import datetime
from analysis.scanner import analyze_fixtures

async def main():
    date_str = "2026-09-05"
    print(f"Scanning {date_str}...")
    predictions = await analyze_fixtures(date_str)
    print(f"Found {len(predictions)} matches.")

if __name__ == "__main__":
    asyncio.run(main())
