#!/usr/bin/python
#-*- coding: UTF-8 -*-
import sys
reload(sys)
sys.setdefaultencoding("utf8")
import urllib2
import threading
import Queue
import os
import pp

if len(sys.argv)!=6:
    print "usage:ziroom.py cores thread lon lat outfile"
    os._exit(0)

originLocation = (float(sys.argv[3]),float(sys.argv[4]))

taskQueue = Queue.Queue()
resultQueue=Queue.Queue()
fout=open(sys.argv[5],"w")
job_server = pp.Server(int(sys.argv[1]))
print job_server.get_ncpus(), "workers"

opener = urllib2.build_opener()
opener.addheaders.append(('User-Agent',' Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.80'))

def generalTask():
    lastPageIndex = 0
    while True:
        if taskQueue.qsize()==0:
            print "current : "+str(lastPageIndex)
            for i in range(0,100):
                taskQueue.put(lastPageIndex)
                lastPageIndex+=1

        threading._sleep(1)
threading.Thread(target= generalTask,args= ()).start()

def writeTask():
    while True:
        line=resultQueue.get(block=True)
        fout.write(line+"\n")
        fout.flush()
        print line
threading.Thread(target= writeTask,args= ()).start()

def httpHelper(url):
    redo = True
    data = None
    redoTime=0
    while redo:
        try:
            data=opener.open(url,timeout=30).read()
            data=data.encode('utf8')
            redo = False
        except:
            print str(redoTime)+" http error",url
            redo = True
            redoTime+=1
    return data

def paraseToGetDetailUrl(html):
    from bs4 import BeautifulSoup
    urls=[]
    soup = BeautifulSoup(html,"html.parser")
    for i in soup.select(".t1"):
        urls.append(i.attrs["href"])
    return urls

def paraseToGetDetail(html,originLocation):
    from bs4 import BeautifulSoup
    from haversine import haversine
    import sys
    reload(sys)
    sys.setdefaultencoding("utf8")
    data={}
    soup = BeautifulSoup(html,"html.parser")
    room_name=soup.select(".room_name > h2")[0].string.strip()
    price=soup.select(".room_price")[0].string[1:]
    lon=soup.select("#mapsearchText")[0].attrs["data-lng"]
    lat=soup.select("#mapsearchText")[0].attrs["data-lat"]
    isShare=soup.select(".icons")[0].string
    priceType=soup.select(".price .gray-6")[0].string
    status="已入住"
    if isShare!="整":
        for item in soup.select(".current .tags"):
            if item.string=="当前房源":
                status="可租"
                break
    else:
        status="可租"
    detail_rooms=soup.select(".detail_room > li")
    space=detail_rooms[0].contents[1].strip()[4:-1]
    dirction=detail_rooms[1].contents[1].strip()[4:]
    struct=detail_rooms[2].contents[1].strip()[4:]
    floor=detail_rooms[3].contents[1].strip()[4:-1]
    floor=floor.replace("/",",")
    dis=str(haversine(originLocation, (float(lon),float(lat))))
    data["room_name"]=room_name
    data["price"]=price
    data["lon"]=lon
    data["lat"]=lat
    data["space"]=space
    data["dirction"]=dirction
    data["struct"]=struct
    data["floor"]=floor
    data["dis"]=dis
    data["isShare"]=isShare
    data["priceType"]=priceType
    data["status"]=status
    return data

def getRoomDetail(rurl):
    data=None
    try:
        url="http://www.ziroom.com/"+rurl
        html=httpHelper(url)
        data=job_server.submit(paraseToGetDetail, (html,originLocation), (), ("bs4","haversine","sys"))
    except:
        print "error2 "+url
    return data

def myTask():
    while True:
        try:
            url="http://www.ziroom.com/z/nl/?p="+str(taskQueue.get(block=True))
            html=httpHelper(url)
            urls=job_server.submit(paraseToGetDetailUrl, (html,), (), ("bs4",))
            for i in urls():
                data=getRoomDetail(i)()
                line=",".join(["http://www.ziroom.com"+i,data["room_name"],data["price"],data["priceType"],data["isShare"],data["lon"],data["lat"],data["space"],data["dirction"],data["struct"],data["floor"],data["dis"],data["status"]])
                resultQueue.put(line)
        except:
            print "error "+url

for i in range(0,int(sys.argv[2])):
    threading.Thread(target= myTask,args= ()).start()
print "thread init done!"