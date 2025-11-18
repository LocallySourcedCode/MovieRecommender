from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = "sqlite:///./app.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def init_db():
    SQLModel.metadata.create_all(engine)

def ensure_tables(session: Session):
    # Ensure tables exist for the current session/connection (helps with in-memory test DBs)
    try:
        # Prefer the actual Connection bound to this Session, so the same in-memory DB is used
        conn = session.connection()
        SQLModel.metadata.create_all(conn)
    except Exception:
        # Fallback to engine bind
        bind = session.get_bind()
        if bind is not None:
            SQLModel.metadata.create_all(bind)


def get_session():
    with Session(engine) as session:
        yield session
