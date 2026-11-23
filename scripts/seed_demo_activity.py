from apps.api.core.config import get_settings
from apps.api.core.database import make_engine, make_session_factory
from apps.api.demo_activity import seed_demo_activity


def main() -> None:
    engine = make_engine(get_settings().database_url)
    session_factory = make_session_factory(engine)
    with session_factory() as db:
        seed_demo_activity(db)
    engine.dispose()
    print("Seeded seven days of fictional demo activity.")


if __name__ == "__main__":
    main()
