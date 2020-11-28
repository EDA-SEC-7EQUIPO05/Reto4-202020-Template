"""
 * Copyright 2020, Departamento de sistemas y Computación
 * Universidad de Los Andes
 *
 *
 * Desarrolado para el curso ISIS1225 - Estructuras de Datos y Algoritmos
 *
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 * Contribución de:
 *
 * Dario Correal
 *
 """
import config
from DISClib.calculos import distances as c
from datetime import date
from datetime import datetime
import datetime
from math import inf
from DISClib.ADT.graph import gr
from DISClib.ADT import map as m
from DISClib.ADT import list as lt
from DISClib.DataStructures import listiterator as it
from DISClib.ADT import stack as st
from DISClib.Algorithms.Graphs import scc
from DISClib.Algorithms.Graphs import dijsktra as djk
from DISClib.Utils import error as error
from DISClib.Algorithms.Graphs import bfs as at
from DISClib.Algorithms.Graphs import dfo as wt
from DISClib.Algorithms.Graphs import dfs as xt
from DISClib.DataStructures import graphstructure as mt
from DISClib.DataStructures import mapentry as me
from itertools import zip_longest
assert config

"""
En este archivo definimos los TADs que vamos a usar y las operaciones
de creacion y consulta sobre las estructuras de datos.
"""

# -----------------------------------------------------
#                       API
# -----------------------------------------------------

def newAnalyzer():
    """ Inicializa el analizador
   graph: Grafo para representar las rutas entre estaciones
    """
    try:
        citibike = {
                    'graph': None, 
                    'Num': 0,
                    "salida": None,
                    "llegada": None,
                    "ubication": None,
                    "trips": None,
                    "bikeID": None

                    }

        citibike['graph'] = gr.newGraph(datastructure='ADJ_LIST',
                                              directed=True,
                                              size=1000,
                                              comparefunction=compareStations) 

        citibike["salida"] = m.newMap(numelements=2000,
                                              maptype="PROBING",
                                              comparefunction=compareStations) 
        citibike["llegada"] = m.newMap(numelements=2000,
                                              maptype="PROBING",
                                              comparefunction=compareStations)
        citibike['trips'] = m.newMap(numelements=1000,
                                        maptype='CHAINING',
                                        comparefunction=compareStations)
        citibike["ubication"] = m.newMap(numelements = 1000, maptype = 'CHAINING', loadfactor = 2, comparefunction = compareStations)
         
        citibike["bikeID"] = m.newMap(numelements = 50000, maptype = 'CHAINING', loadfactor = 2, comparefunction = compareStations)
        
        return citibike
    except Exception as exp:
        error.reraise(exp, 'model:newAnalyzer')

# Funciones para agregar informacion al grafo

def addTrip (citibike, trip):
    """
    """
    origin = trip["start station id"]
    destination = trip["end station id"]
    lat_origin = str(trip["start station latitude"])
    lon_origin = str(trip["start station longitude"])
    lat_destination = str(trip["end station latitude"])
    lon_destination = str(trip["end station longitude"])
    duration = int(trip["tripduration"])
    birthDate = int(trip["birth year"])
    user = trip["usertype"]
    date = trip["starttime"]
    date = date.split(" ")
    date1 = date[0].split("-")
    date1 = "".join(date1)
    date2 = date[1].split(":")
    date2 = "".join(date2)
    date = date1 + date2
    bikeID = trip["bikeid"]
    if user == 'Customer':
        user = True
    else:
        user = False
    age = ageCalculator(birthDate)
    addStation(citibike,origin)
    addStation(citibike,destination)
    addConnection(citibike,origin,destination,duration,age,user)
    addUbication(citibike, origin, lon_origin, lat_origin)
    addUbication(citibike, destination, lon_destination, lat_destination)
    addAgeTrip(citibike,origin,destination,age)
    addBikeID(citibike, bikeID, date, duration, origin)
    citibike['Num'] += 1

def addStation (citibike,stationId):
    """
    Adiciona una estación como un vertice del grafo
    """
    if not gr.containsVertex (citibike["graph"], stationId):
        gr.insertVertex( citibike["graph"],stationId)
    if not m.contains(citibike["salida"],stationId):
        m.put(citibike["salida"],stationId,{"salidas":0})
    if not m.contains(citibike["llegada"],stationId):
        m.put(citibike["llegada"],stationId,{"llegadas":0})
    if not m.contains(citibike["trips"], stationId):
        originAgeMap = m.newMap(numelements=10, maptype='CHAINING', comparefunction=compareAges)
        destinyAgeMap = m.newMap(numelements=10, maptype='CHAINING', comparefunction=compareAges)
        m.put(citibike["trips"], stationId, {'salidas': {'num': 0, 'age': originAgeMap}, 'llegadas':  {'num': 0, 'age': destinyAgeMap}})
    return citibike

def addConnection (citibike,origin,destination,duration,age,user):
    """
    Adiciona un arco entre dos estaciones 
    """
    originEntry= me.getValue(m.get(citibike["salida"],origin))
    originEntry["salidas"]+=1
    destinyEntry=me.getValue(m.get(citibike["llegada"],destination))
    destinyEntry["llegadas"] +=1
    originEntry1 = me.getValue(m.get(citibike['trips'], origin))
    originEntry1['salidas']['num'] += 1
    destinyEntry1 = me.getValue(m.get(citibike['trips'], destination))
    destinyEntry1['llegadas']['num'] += 1
    edge = gr.getEdge(citibike ["graph"], origin, destination)
    if edge is None:
        weight = [duration, 1]
        ageMap = newAgeMap()
        gr.addEdge(citibike["graph"], origin, destination, weight)
        edge = gr.getEdge(citibike["graph"], origin, destination)
        edge['age'] = ageMap
        if user:
            edge_1 = gr.getEdge(citibike["graph"], origin, destination)
            Entry = m.get(edge_1['age'], representativeAge(age))
            Value = Entry['value']
            Value['num'] += 1
    else:
        edge['weight'][0] = (edge['weight'][0]*edge['weight'][1] + duration)/(edge['weight'][1] + 1)
        edge['weight'][1] += 1
        if user:
            ageMapEntry = me.getValue(m.get(edge['age'], representativeAge(age)))
            ageMapEntry['num'] += 1

    return citibike

def addUbication(citibike, stationId, lon, lat):
    if not m.contains(citibike["ubication"], stationId):
        m.put(citibike["ubication"], stationId, [lon, lat, stationId])

def newAgeMap():
    ageMap = m.newMap(numelements=8,maptype='CHAINING',loadfactor=2,comparefunction=compareAges)
    for i in range(5,75,10):
        m.put(ageMap, representativeAge(i), {'num': 0})
    return ageMap

def addtrips (citibke,stationId):
     try:
        if not gr.containsVertex(citibke['graph'], stationId):
            gr.insertVertex(citibke['graph'], stationId)
        return analyzer
     except Exception as exp:
        error.reraise(exp, 'model:addstop')

def addAgeTrip(citibike, origin, destination, age):
    rep_age = representativeAge(age)
    originAgeMap = me.getValue(m.get(citibike['trips'], origin))['salidas']['age']
    destinyAgeMap = me.getValue(m.get(citibike['trips'], destination))['llegadas']['age']
    if not m.contains(originAgeMap, rep_age):
        m.put(originAgeMap, rep_age, {'num': 1})
    else:
        me.getValue(m.get(originAgeMap, rep_age))['num'] += 1
    if not m.contains(destinyAgeMap, rep_age):
        m.put(destinyAgeMap, rep_age,{'num': 1})
    else:
        me.getValue(m.get(destinyAgeMap, rep_age))['num'] += 1

def addBikeID(citibike, bikeID, date, duration, stationID):
    if not m.contains(citibike["bikeID"], bikeID):
        info = [[[date, stationID]], [duration]]
        m.put(citibike["bikeID"],  bikeID, [info, bikeID])
    else:
        entry = m.get(citibike["bikeID"],  bikeID)
        value = me.getValue(entry)
        infoo = value[0]
        infoo[0].append([date, stationID])
        infoo[1].append(duration)

# ==============================
# Funciones de consulta
# ==============================

def totalTrips(citibike):
    return citibike['Num']

def totalConnections(citibike):
    graph = citibike["graph"]
    return gr.numEdges(graph)

def totalStations(citibike):
    graph = citibike["graph"]
    return gr.numVertices(graph)

def req1(citibike, station1, station2):
    clusters = scc.KosarajuSCC(citibike['graph'])
    num = numClusters(clusters)
    connected = sameCluster(clusters, station1, station2)
    return (num, connected)

def numClusters(clusters):
    return scc.connectedComponents(clusters)

def sameCluster(clusters, station1, station2):
    return scc.stronglyConnected(clusters, station1, station2)

def req3primero (citibike):
    lista=[]
    lista2=[]
    lista3=[]
    llaves=m.keySet(citibike["salida"])
    valores=m.valueSet(citibike["salida"])
    iterator_llaves=it.newIterator(llaves)
    iterator_valores=it.newIterator(valores)
    while it.hasNext(iterator_llaves) and it.hasNext(iterator_valores):
        key = it.next(iterator_llaves)
        value = it.next(iterator_valores)
        lista.append(value)
        lista2.append([key,value])

    for i in lista:
        valor=i
        for k in valor:
            numeros=valor[k]
            lista3.append(numeros)
    lista3.sort()
    mayor=max(lista3)
    eliminacion=lista3.remove(mayor)
    mayor1=max(lista3)
    eliminacion1=lista3.remove(mayor1)
    mayor2=max(lista3)

    for i in lista:
        valor=i
        for k in valor:
            numeros=valor[k]
            if numeros==mayor:
                respuesta=valor
            elif numeros==mayor1:
                respuesta1=valor
            elif numeros==mayor2:
                respuesta2=valor

    final=respuesta
    final1=respuesta1
    final2=respuesta2

    for u in lista2:
        valor=u
        for v in valor:
            solucion=v
            opcion=final
            opcion1=final1
            opcion2=final2
            if solucion==opcion:
                ultima=valor
            elif solucion==opcion1:
                ultima1=valor
            elif solucion==opcion2:
                ultima2=valor
    return (ultima[0],ultima1[0],ultima2[0])

def req3segundo (citibike):
    lista=[]
    lista2=[]
    lista3=[]
    llaves=m.keySet(citibike["llegada"])
    valores=m.valueSet(citibike["llegada"])
    iterator_llaves=it.newIterator(llaves)
    iterator_valores=it.newIterator(valores)
    while it.hasNext(iterator_llaves) and it.hasNext(iterator_valores):
        key = it.next(iterator_llaves)
        value = it.next(iterator_valores)
        lista.append(value)
        lista2.append([key,value])

    for i in lista:
        valor=i
        for k in valor:
            numeros=valor[k]
            lista3.append(numeros)
    lista3.sort()
    mayor=max(lista3)
    eliminacion=lista3.remove(mayor)
    mayor1=max(lista3)
    eliminacion1=lista3.remove(mayor1)
    mayor2=max(lista3)

    for i in lista:
        valor=i
        for k in valor:
            numeros=valor[k]
            if numeros==mayor:
                respuesta=valor
            elif numeros==mayor1:
                respuesta1=valor
            elif numeros==mayor2:
                respuesta2=valor

    final=respuesta
    final1=respuesta1
    final2=respuesta2

    for u in lista2:
        valor=u
        for v in valor:
            solucion=v
            opcion=final
            opcion1=final1
            opcion2=final2
            if solucion==opcion:
                ultima=valor
            elif solucion==opcion1:
                ultima1=valor
            elif solucion==opcion2:
                ultima2=valor
    return (ultima[0],ultima1[0],ultima2[0])
  
def req3tercero (citibike):
    dic={}
    lista=[]
    lista2=[]
    lista5=[]
    llaves=m.keySet(citibike["llegada"])
    valores=m.valueSet(citibike["llegada"])
    iterator_llaves=it.newIterator(llaves)
    iterator_valores=it.newIterator(valores)
    while it.hasNext(iterator_llaves) and it.hasNext(iterator_valores):
        key = it.next(iterator_llaves)
        value = it.next(iterator_valores)
        lista.append(value)
        lista2.append([key,value])

    for i in lista:
        valor=i
        for k in valor:
            numeros=valor[k]
            lista5.append(numeros)

    lista3=[]
    lista4=[]
    lista6=[]
    llaves1=m.keySet(citibike["salida"])
    valores1=m.valueSet(citibike["salida"])
    iterator_llaves1=it.newIterator(llaves1)
    iterator_valores1=it.newIterator(valores1)
    while it.hasNext(iterator_llaves1) and it.hasNext(iterator_valores1):
        key1 = it.next(iterator_llaves1)
        value1 = it.next(iterator_valores1)
        lista3.append(value1)
        lista4.append([key1,value1])

    for i in lista:
        valor=i
        for k in valor:
            numeros=valor[k]
            lista6.append(numeros)
    
    mayor, menor = (lista5, lista6) if len(lista5) >= len(lista6) else (lista6, lista5)
    lista7=[]
    for i, _ in enumerate(mayor):
        if i + 1 > len(menor):
            lista7.append(mayor[i])
        else:
            lista7.append(mayor[i] + menor[i])

    lista8=[]
    for i in lista7:
        dic[key]=dic.get(key,i)
        lista8.append(dic)
    
    return lista8

def req4(citibike, station, time):
    search = dfsParcial(citibike["graph"], station, time)
    return routeList(citibike["graph"], search, station)

def req5(citibike, age):
    max_in = 0
    max_in_st = None
    max_in_2 = 0
    max_in_st_2 = None
    max_out = 0
    max_out_st = None
    rep_age = representativeAge(age)
    stations = m.keySet(citibike['trips'])
    stationIterator = it.newIterator(stations)
    while it.hasNext(stationIterator):
        elem = it.next(stationIterator)
        salidaEntry = m.get(me.getValue(m.get(citibike['trips'], elem))['salidas']['age'], rep_age)
        llegadaEntry = m.get(me.getValue(m.get(citibike['trips'], elem))['llegadas']['age'], rep_age)
        if salidaEntry is None:
            salida = 0
        else: 
            salida = me.getValue(salidaEntry)['num']
        if llegadaEntry is None:
            llegada = 0
        else:
            llegada = me.getValue(llegadaEntry)['num']
        if salida > max_out:
            max_out = salida
            max_out_st = elem
        if llegada > max_in:
            max_in_2 = max_in
            max_in_st_2 = max_in_st
            max_in = llegada
            max_in_st = elem
    if max_in_st == max_out_st:
        max_in_st = max_in_st_2
    if max_in_st is None or max_out_st is None:
        return None
    elif shortRoute(citibike, max_out_st, max_in_st) is not None:
        return True, shortRoute(citibike, max_out_st, max_in_st)
    else:
        return False, max_out_st, max_in_st

def req6(citibike, lon1, lat1, lon2, lat2):
    mapa = {
        "masCercanaStart": None,
        "masCercanaEnd": None,
        "tiempo": 0,
        "estaciones": None
    }
    StartStation = estacionMasCercana(citibike, lon1, lat1)
    EndStation = estacionMasCercana(citibike, lon2, lat2)
    search = djk.Dijkstra(citibike["graph"], StartStation)
    if djk.hasPathTo(search, EndStation):
        mapa["tiempo"] = str(djk.distTo(search, EndStation))
        mapa["estaciones"] = djk.pathTo(search, EndStation)
    else:
        mapa["tiempo"] = "Infinito"
    mapa["masCercanaStart"] = StartStation
    mapa["masCercanaEnd"] = EndStation
    return mapa

def estacionMasCercanaStart(mapa):
    return mapa["masCercanaStart"]

def estacionMasCercanaEnd(mapa):
    return mapa["masCercanaEnd"]

def tiempoRecorrido(mapa):
    return mapa["tiempo"]

def estacionesRecorrido(mapa):
    return mapa["estaciones"]

def req7(citibike, ageRange):
    maxEdges = lt.newList()
    maxEdgeNum = 0
    edges = gr.edges(citibike['graph'])
    edgeIterator = it.newIterator(edges)
    while it.hasNext(edgeIterator):
        edge = it.next(edgeIterator) 
        ageMap = edge['age']
        ageMapEntry = m.get(ageMap, ageRange)
        num = ageMapEntry['value']['num']
        if num == maxEdgeNum:
            lt.addLast(maxEdges, edge)
        elif num > maxEdgeNum:
            maxEdgeNum = num
            maxEdges = lt.newList()
            lt.addLast(maxEdges, edge)
    if maxEdgeNum == 0:
        return None
    else:
        return maxEdges

def req8(citibike, bikeID, date):
    entry = m.get(citibike["bikeID"], bikeID)
    value = me.getValue(entry)
    info = value[0]
    dates = info[0]
    dates.sort()
    min_date = min(dates)[0]
    durations = info[1]
    duration_summations = 0
    for i in durations:
        duration_summations += int(i)
    total_time = daysBetweenDates(date, min_date)
    total_time = total_time.replace(":", " ")
    total_time = total_time.split(" ")
    seconds = list(min_date)
    del seconds[0:12]
    seconds = "".join(seconds)
    total_time = int(total_time[0])*24*60*60 + int(total_time[2])*60*60 + int(total_time[3])*60 + int(total_time[4]) - float(seconds)
    time_estacionada = total_time - duration_summations
    duration_summations = convertSeconds(duration_summations)
    time_estacionada = convertSeconds(time_estacionada)
    return [duration_summations, time_estacionada, dates]
# ==============================
# Funciones Helper
# ==============================

def estacionMasCercana(citibike, lon_user, lat_user):
    station = None
    ubications = m.valueSet(citibike["ubication"])
    iterator = it.newIterator(ubications)
    menor = inf
    while it.hasNext(iterator):
        ubication = it.next(iterator)
        id_station = ubication[2]
        lon_station = ubication[0]
        lat_station = ubication[1]
        lon = abs(float(lon_station) - float(lon_user))
        lat = abs(float(lat_station) - float(lat_user))
        distance = c.calcularDistancia(1, lon, lat)
        if distance < menor:
            menor = distance
            station = id_station
    return station

def dijsktra(citibike, station):
    return djk.Dijkstra(citibike, station)

def dfsParcial(graph, source, time):
    search = {
                  'source': source,
                  'visited': None
                  }

    search['visited'] = m.newMap(numelements=gr.numVertices(graph),
                                       maptype='PROBING',
                                       comparefunction=graph['comparefunction']
                                       )

    m.put(search['visited'], source, {'marked': True, 'edgeTo': None, 'time': 0})
    vertexDepthSearch(search, graph, source, time, True)
    return search

def vertexDepthSearch(search, graph, vertex, time, source):
    adjlst = gr.adjacents(graph, vertex)
    if source:
        adjslstiter = it.newIterator(adjlst)
        while (it.hasNext(adjslstiter)):
            w = it.next(adjslstiter)
            visited = m.get(search['visited'], w)
            if visited is None:
                temp = gr.getEdge(graph, vertex, w)["weight"][0]
                if (temp) <= time:
                    m.put(search['visited'],
                        w, {'marked': True, 'edgeTo': vertex, 'time': temp})
                    vertexDepthSearch(search, graph, w, time, False)
    else:
        if lt.size(adjlst) > 0:
            x = True
            adjslstiter = it.newIterator(adjlst)
            while x and it.hasNext(adjslstiter):
                w = it.next(adjslstiter)
                visited = m.get(search['visited'], w)
                if visited is None:
                    root = me.getValue(m.get(search['visited'], vertex))
                    temp = gr.getEdge(graph, vertex, w)["weight"][0]
                    if (root['time'] + temp) <= time:
                        x = False
                        m.put(search['visited'],
                            w, {'marked': True, 'edgeTo': vertex, 'time': (root["time"] + temp)})
                        vertexDepthSearch(search, graph, w, time, False)
    return search

def routeBuild(graph, search, vertexA, vertexB, keys):
    visited = search["visited"]
    iterator = it.newIterator(keys)
    ruta = ''
    if vertexA == search['source']:
        ruta += vertexA + " --> " + vertexB + " costo: " + str(gr.getEdge(graph, vertexA, vertexB)["weight"][0]) + "\n"
    while it.hasNext(iterator):
        elemento = it.next(iterator)
        if me.getValue(m.get(visited, elemento))["edgeTo"] == vertexB:
            ruta += vertexB + " --> " + elemento + " costo: " + str(gr.getEdge(graph, vertexB, elemento)["weight"][0]) + "\n"
            ruta += routeBuild(graph, search, vertexB, elemento, keys)
    return ruta

def routeList(graph, search, source):
    routes = lt.newList(datastructure="SINGLE_LINKED")
    visited = search["visited"]
    keys = m.keySet(visited)
    iterator = it.newIterator(keys)
    while it.hasNext(iterator):
        elemento = it.next(iterator)
        if me.getValue(m.get(visited, elemento))["edgeTo"] == source:
            lt.addLast(routes, routeBuild(graph, search, source, elemento, keys))
    return routes

def representativeAge(age):
    if age >= 0 and age <= 10:
        return '0-10'
    elif age >= 11 and age <= 20:
        return '11-20'
    elif age >= 21 and age <= 30:
        return '21-30'
    elif age >= 31 and age <= 40:
        return '31-40'
    elif age >= 41 and age <= 50:
        return '41-50'
    elif age >= 51 and age <=60:
        return '51-60'
    else:
        return '60+'

def  ageCalculator(birth_year):
    return 2020-birth_year

def shortRoute(citibike, origin, destination):
    dijs = dijsktra(citibike['graph'], origin)
    path = djk.pathTo(dijs, destination)
    return routeFormat(path)

def routeFormat(path):
    if st.top(path) is None:
        return None
    else:
        listPath = lt.newList(datastructure = 'SINGLE_LINKED')
        while not st.isEmpty(path):
            lt.addLast(listPath, st.pop(path))
        first = lt.firstElement(listPath)
        last = lt.lastElement(listPath)
        route = {'first': first, 'last': last, 'route': listPath}
        return route

def daysBetweenDates(date1, date2):
    date1 = date1.split("-")
    start = datetime.datetime(int(date2[:4]),int(date2[4:6]),int(date2[6:8]),int(date2[8:10]),int(date2[10:12]))
    end   = datetime.datetime(int(date1[0]),int(date1[1]),int(date1[2]),00,00)
    delta = str(end-start)
    return delta

def convertSeconds(seconds): 
    day = seconds // (24 * 3600)
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    seconds = seconds
    return "d:h:m:s-> %d:%d:%d:%d" % (day, hour, minutes, seconds)

# ==============================
# Funciones de Comparacion
# ==============================

def compareStations (stop,
keyvaluestop):
    """
    Compara dos estaciones
    """
    stopcode = keyvaluestop['key']
    if (stop == stopcode):
        return 0
    elif (stop > stopcode):
        return 1
    else:
        return -1

def compareAges(age, keyvalueage):
    agecode = keyvalueage['key']
    if age == agecode:
        return 0
    elif age > agecode:
        return 1
    else:
        return -1