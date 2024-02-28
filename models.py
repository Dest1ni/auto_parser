from sqlalchemy import ForeignKey, create_engine,Column,Integer,String
from sqlalchemy.orm import sessionmaker,Session as SessionType,scoped_session,declarative_base,declared_attr
from sqlalchemy_utils import ChoiceType


#engine = create_engine(url="postgresql+psycopg2://postgres:postgres@localhost:5432/auto")
engine = create_engine(url="sqlite:///auto.db")
maker=sessionmaker(bind=engine)
Session=scoped_session(maker)

class Base():
    """
    Базовая модель
    """
    __bind_key__ = engine
    @declared_attr
    def __tablename__(cls):
        return f'{cls.__name__.lower()}s'
    id = Column(Integer,primary_key=True)
    
Base = declarative_base(cls=Base)

 
class Route(Base):
    """
    Объект маршрута
    """
    name = Column(String(244), nullable=False)


class Station(Base):
    """
    Объект станции
    """
    name = Column(String(244), nullable=False)
    
class RouteStationAT(Base):
    """
    Связь маршута с станцией
    """
    route_id = Column(Integer,ForeignKey(f'{Route.__tablename__}.id'),nullable=False)
    station_id = Column(Integer,ForeignKey(f'{Station.__tablename__}.id'),nullable=False)

class StopTime(Base):
    """
    Время остановки маршрута на станции
    """
    time = Column(String(5),nullable=False)
    TYPES = [('weekday','weekday'),('weekend','weekend')]
    day = Column(ChoiceType(TYPES),nullable=False)
    route_station_at_id = Column(Integer,ForeignKey(f'{RouteStationAT.__tablename__}.id'),nullable=False)


def create_db():
    """
    Создает все таблицы в БД
    """
    Base.metadata.create_all(bind=engine)

def drop_db():
    """
    Удаляет все таблицы в БД
    """
    Base.metadata.drop_all(bind=engine)

if __name__=="__main__":
    session: SessionType = Session()
    drop_db()
    create_db()
    session.close()