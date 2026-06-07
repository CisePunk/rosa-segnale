import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ROOT = PROJECT_ROOT / "backend"

sys.path.insert(0, str(BACKEND_ROOT))

from app.report_scheduler import write_weekly_report_files  # noqa: E402
from app.repository import init_db  # noqa: E402


def main() -> None:
    init_db()
    output_path = write_weekly_report_files()
    print(f"Weekly report written to {output_path}")


if __name__ == "__main__":
    main()
