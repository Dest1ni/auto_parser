from bs4 import BeautifulSoup as BS
import requests
from models import *
from sqlalchemy import and_, asc, insert,select
import re
import datetime

from sqlalchemy.orm import aliased
from sqlalchemy import and_

def get_routes(url:str) -> dict:
    """ 
    Возвращает остановки (И url для этих остановок) в двух напрявлениях (При наличии обратного), 
    если обратного маршрута нет, возварщает остановки прямого маршрута
    ВНИМАНИЕ !
    Если маршрут кольцевой то он воспринимается как маршрут юдущий только в одном направлении
    """
    #Поиск правой таблицы
    answer = dict()
    r = requests.get("https://gomeltrans.net" + url)
    html = BS(r.content,'html.parser')
    routes_divs_r = html.find_all('td', class_='t-right')
    if routes_divs_r:
        name = html.find_all("td",class_ = "t-right") # Поиск всех направлений маршрута в правом столбце
        for nam in name: 
            nams = nam.find_all("td",class_ = "route-stop1")
            for i in nams:
                current = re.sub(r'\s+', ' ', i.text.strip()) # Чистое направление маршрута
                answer[current] = list() # Направление маршрута
        for div in routes_divs_r:
            route_route = div.find_all('a')
            for link in route_route:
                answer[current].append(link)
                
        #Поиск левой таблицы
        routes_divs_l = html.find_all('td', class_='t-left')
        name = html.find_all("td",class_ = "t-left")
        for nam in name:
            nams = nam.find_all("td",class_ = "route-stop1")
            for i in nams:
                if re.sub(r'\s+', ' ', i.text.strip()) not in answer: # Чистое направление маршрута
                    current_left = re.sub(r'\s+', ' ', i.text.strip())
                    answer[current_left] = list() # Направление маршрута 
        for div in routes_divs_l:
            route_route = div.find_all('a')
            for link in route_route[0:len(route_route)-len(answer[current])]:
                answer[current_left].append(link)
        return answer
    else:
        name = html.find_all("td",class_ = "t-left")
        routes_divs_l = html.find_all('td', class_='t-left')
        for nam in name: # Поиск всех направлений маршрута в левом столбце (Работает не окей, всегда выбивает и правый столб)
            nams = nam.find_all("td",class_ = "route-stop1") 
            for i in nams:
                current = re.sub(r'\s+', ' ', i.text.strip())
                answer[current] = list() # Направление маршрута
        for div in routes_divs_l:
            route_route = div.find_all('a')
            for link in route_route:
                answer[current].append(link)        
        return answer

def get_time(url:str) -> dict[dict[list[str]]]:
    """
    Выдаёт время остановки на конкретной остановке по url остановки
    {'weekday':['5:34'],'weekend':['2:30']}
    """
    watch = {"weekday":[],"weekend":[]}
    r = requests.get("https://gomeltrans.net" + url)
    html = BS(r.content,'html.parser')
    hour = html.find_all('div',class_ = "schedule-graphic")
    for i in hour:
        if i.find('h2',class_='schedule-graphic-name day-off'):
            x = i.find_all('div',class_ = "sch-m")
            for j in x:
                watch['weekend'].append(f"{j.find_parent().find_previous().text.strip()}:{j.text.strip()}")
        elif i.find('h2',class_='schedule-graphic-name week-day'):
            x = i.find_all('div',class_ = "sch-m")
            for j in x:
                watch["weekday"].append(f"{j.find_parent().find_previous().text.strip()}:{j.text.strip()}")
    return watch

def get_similar_station(text:str) -> set[str]:
    """
    Выдаёт похожие по написанию остановки
    """
    session = Session()
    stmt = select(Station).where(Station.name.like(f"%{text}%"))
    stations = session.execute(stmt).fetchall()
    answer = set()
    for objects in stations:
        for object in objects:
            answer.add(object.name)
    session.close()
    return answer

def is_dayoff() -> int:
    """
    Возвращает выходной ли день.
    0 - Рабочий
    1 - Выходной
    """
    date = str(datetime.datetime.today())

    y,m,d = date[0:11].split('-')
    r = requests.get(f"https://isdayoff.ru/{y}{m}{d}?cc=by".strip())
    return r.content

def get_routes_by_two_stations(current:str,finish:str) -> list:
    """
    Выдаёт все доступные маршруты по двум станциям
    """
    session = Session()
    routes_current = session.query(RouteStationAT.route_id).\
    join(Station, Station.id == RouteStationAT.station_id).\
    filter(Station.name == current).subquery()

    routes_finish = session.query(RouteStationAT.route_id).\
        join(Station, Station.id == RouteStationAT.station_id).\
        filter(Station.name == finish).subquery()

    routes_with_both_stations = session.query(Route).\
        join(RouteStationAT, Route.id == RouteStationAT.route_id).\
        filter(RouteStationAT.route_id.in_(routes_current)).\
        filter(RouteStationAT.route_id.in_(routes_finish)).all()
    answer = list()
    for route in routes_with_both_stations:
        route_name = route.name
        stations = session.query(Station).\
            join(RouteStationAT, Station.id == RouteStationAT.station_id).\
            join(Route, Route.id == RouteStationAT.route_id).\
            filter(Route.name == route_name).all()
        stations = [x.name for x in stations]
        if stations.index(current) < stations.index(finish):
            answer.append(route)
    session.close()
    return answer

def get_current_time():
    time = datetime.datetime.time(datetime.datetime.now())
    return time

def get_closest_routes(current: str, finish: str):
    """
    Выдаёт ближайшие маршруты в виде:
    {"Маршрут": "Ближайшее время прибытия"}
    """
    session = Session()
    valid_routes = get_routes_by_two_stations(current=current, finish=finish)
    answer = {}
    alls = list()
    if not is_dayoff():
        day = "weekend"
    else:
        day = "weekday"
    for route in valid_routes:
        alls.append(session.query(RouteStationAT).\
        join(Station, Station.id == RouteStationAT.station_id).\
        filter(RouteStationAT.route_id == route.id).\
        filter(Station.name == current).all())
    alls = [x[0] for x in alls]
    for i in alls:
        route = session.query(Route).filter_by(id = i.route_id).first().name
        answer[route] = None
        times = session.query(StopTime).filter_by(route_station_at_id = i.id).filter_by(day = day).all()
        for time in times:
            time_array = (time.time).split(":")
            if datetime.time(int(time_array[0]),int(time_array[1])) > get_current_time():
                make_pretty = str(datetime.time(int(time_array[0]),int(time_array[1]))).split(":")
                answer[route] =  f"{make_pretty[0].lstrip('0')}:{make_pretty[1]}"
                break
    session.close()
    return answer


if __name__ == "__main__":
    session = Session()
    print(get_closest_routes(current="Предприятие «Коминтерн»",finish="Солнечная"))
    session.close()