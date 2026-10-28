from apps.api.core.config import get_settings
from apps.api.core.database import make_engine, make_session_factory
from apps.api.seed import seed


def main() -> None:
    engine = make_engine(get_settings().database_url)
    session_factory = make_session_factory(engine)
    with session_factory() as db:
        seed(db)
    engine.dispose()
    print("Seeded demo accounts and meals, sourced venues, discussions and exercises.")


if __name__ == "__main__":
    main()
