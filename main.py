from bs4 import BeautifulSoup as BS
import requests
from models import *
from sqlalchemy import insert
from router import *
from loguru import logger

def total_parse() -> None:
    """
    Парсит все городские автобусные маршруты
    """
    r = requests.get("https://gomeltrans.net/routes/bus/")
    html = BS(r.content,'html.parser')

    routes_divs = html.find_all('div', class_='routes-list')
    for div in routes_divs: 
        route_links = div.find_all('a')
        for link in route_links: # Получаем все маршруты вместе с их ссылками
            route_number = link.text.strip().split()[0] # Название основного маршрута
            route_url = link['href']
            answer = get_routes(route_url)
            for key,value in answer.items(): # Key чистый value - html-ка, key это подмаршрут
                stmt = insert(Route).values(name = route_number + " " + key)
                route_pk: int = session.execute(stmt.returning(Route.id)).scalar() #pk
                session.commit() 
                for station in value:
                    stmt_station = insert(Station).values(name = station.text.strip())
                    station_pk: int = session.execute(stmt_station.returning(Station.id)).scalar() # pk стацнии
                    stmt_route_station_at = insert(RouteStationAT).values(route_id=route_pk,station_id=station_pk)
                    route_station_at_pk = session.execute(stmt_route_station_at.returning(RouteStationAT.id)).scalar() #pk RSAT
                    session.commit()
                    watch: dict = get_time(station["href"]) 
                    for key_w,value_w in watch.items():
                        for time in value_w:
                            stmt_watch = insert(StopTime).values(route_station_at_id = route_station_at_pk, time = time,day = key_w)
                            session.execute(stmt_watch)
                            session.commit()
                logger.success(f"Маршрут {route_number} спаршен")
        logger.success("Все маршруты спаршены")

if __name__ == "__main__":
    session = Session()
    total_parse()
    session.close()