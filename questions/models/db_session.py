import sqlalchemy as sa
import sqlalchemy.ext.declarative as dec
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session

SqlAlchemyBase = dec.declarative_base()

# Global variable to store the SQLAlchemy session factory
__factory = None


def global_init(db_file, drop_db=False):
    """
    Initialize the global SQLAlchemy session factory and create or drop/create database tables.

    Args:
        db_file (str): The path to the SQLite database file.
        drop_db (bool): Whether to drop and recreate the database tables.

    Raises:
        Exception: If the database file is not provided.
    """
    global __factory

    if __factory and not drop_db:
        return

    if not db_file or not db_file.strip():
        raise Exception("Необходимо указать файл базы данных.")

    # Create a connection string for SQLite
    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'
    print(f"Подключение к базе данных по адресу {conn_str}")

    # Create an SQLAlchemy engine and session factory
    engine = sa.create_engine(conn_str, echo=False)

    if drop_db:
        # Drop all tables if specified
        SqlAlchemyBase.metadata.drop_all(engine)

    # Create database tables if they don't exist
    SqlAlchemyBase.metadata.create_all(engine)

    __factory = orm.sessionmaker(bind=engine)


def create_session() -> Session:
    """
    Create a new SQLAlchemy session.

    Returns:
        Session: A new SQLAlchemy session.

    Raises:
        AttributeError: If the session factory is not initialized.
    """
    global __factory

    # Ensure the session factory is initialized
    if not __factory:
        raise AttributeError("Session factory is not initialized.")

    # Create and return a new session
    return __factory()
