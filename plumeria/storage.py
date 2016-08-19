from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from . import config
from .event import bus

url = config.create("storage", "url",
                    comment="The engine connection URL in the format of:\n"
                            "  dialect+driver://username:password@host:port/database\n\n"
                            "Examples:\n"
                            "  postgresql://username:password@localhost/mydatabase\n"
                            "  postgresql+psycopg2://username:password@localhost/mydatabase\n"
                            "  mysql://username:password@localhost/foo\n"
                            "  sqlite:///example.db")

Base = declarative_base()
Session = sessionmaker()


@bus.event('preinit')
async def preinit():
    engine = create_engine(url(), echo=True)
    Session.configure(bind=engine)
