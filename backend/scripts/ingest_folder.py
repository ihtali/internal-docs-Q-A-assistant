#!/usr/bin/env python3
import json
import sys

from app.db import SessionLocal, init_db
from app.ingest import ingest_folder


def main() -> None:
    init_db()
    folder = sys.argv[1] if len(sys.argv) > 1 else "documents"
    with SessionLocal() as session:
        result = ingest_folder(folder, session)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
