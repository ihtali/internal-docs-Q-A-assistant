from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    from app.models import Chunk, Document  # noqa: F401

    if engine.url.get_backend_name() != "sqlite":
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

            table_exists = conn.execute(
                text(
                    "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'chunks')"
                )
            ).scalar()
            if table_exists:
                column_type = conn.execute(
                    text(
                        """
                        SELECT data_type
                        FROM information_schema.columns
                        WHERE table_name = 'chunks' AND column_name = 'embedding'
                        """
                    )
                ).scalar()
                if column_type in {"text", "ARRAY"}:
                    conn.execute(
                        text(
                            f"""
                            ALTER TABLE chunks
                            ALTER COLUMN embedding TYPE vector({settings.EMBEDDING_DIMENSION})
                            USING embedding::vector
                            """
                        )
                    )

    Base.metadata.create_all(bind=engine)
