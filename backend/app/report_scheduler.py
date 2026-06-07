import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path

from app.repository import generate_weekly_report


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = Path(os.getenv("REPORTS_DIR", PROJECT_ROOT / "reports"))
DEFAULT_INTERVAL_SECONDS = 7 * 24 * 60 * 60


async def weekly_report_loop() -> None:
    interval_seconds = int(os.getenv("AUTO_WEEKLY_REPORT_INTERVAL_SECONDS", str(DEFAULT_INTERVAL_SECONDS)))

    while True:
        await asyncio.to_thread(write_weekly_report_files)
        await asyncio.sleep(interval_seconds)


def write_weekly_report_files() -> Path:
    report = generate_weekly_report()
    REPORTS_DIR.mkdir(exist_ok=True)

    latest_path = REPORTS_DIR / "weekly_report_latest.md"
    latest_path.write_text(report.markdown + "\n", encoding="utf-8")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    archive_path = REPORTS_DIR / f"weekly_report_{timestamp}.md"
    archive_path.write_text(report.markdown + "\n", encoding="utf-8")

    return latest_path
