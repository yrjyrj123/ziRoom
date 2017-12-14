# coding=utf-8
import requests
import Queue
import json
import zipfile

API_URL = "http://www.ziroom.com/map/room/list?min_lng=%.6f&max_lng=%.6f&min_lat=%.6f&max_lat=%.6f&p=%d"


class Grid():
    def __init__(self, lonlat):  # [lon_min,lon_max,lat_min,lat_max]
        self._lon_min = lonlat[0]
        self._lon_max = lonlat[1]
        self._lat_min = lonlat[2]
        self._lat_max = lonlat[3]
        self._page_one_cache = None

    def __str__(self):
        return "%.6f,%.6f,%.6f,%.6f" % tuple(self.get_range())

    def _json_request(self, lonlat, page_index):

        if page_index == 1 and self._page_one_cache is not None:
            return self._page_one_cache

        url = API_URL % (lonlat[0], lonlat[1], lonlat[2], lonlat[3], page_index)
        # print(url)
        while True:
            try:
                json_str = requests.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
                    "Referer": "http://www.ziroom.com/map/"
                }, timeout=1).text
                obj = json.loads(json_str)
                if obj["code"] == 200:
                    obj = json.loads(json_str)
                    self._page_one_cache = obj
                    return obj
                else:
                    print("error %s" % json_str)
            except:
                print("retry " + url)

    def empty(self):
        obj = self._json_request((self._lon_min, self._lon_max, self._lat_min, self._lat_max), 1)
        return len(obj["data"]["rooms"]) == 0

    def area(self):
        return (self._lon_max - self._lon_min) * 1e5 * (self._lat_max - self._lat_min) * 1e5

    def get_rooms(self):
        result = {}
        last_len = -1
        page_index = 1

        useless_count = 0

        while True:
            last_len = len(result.keys())

            obj = self._json_request((self._lon_min, self._lon_max, self._lat_min, self._lat_max), page_index)

            for item in obj["data"]["rooms"]:
                result[item["id"]] = item
            page_index += 1
            if last_len == len(result.keys()):
                useless_count += 1
            if len(obj["data"]["rooms"]) == 0 or useless_count > 3:
                return result

    def split(self, count=2):
        lon_step = (self._lon_max - self._lon_min) / count
        lat_step = (self._lat_max - self._lat_min) / count

        result = []

        for i in range(0, count):
            for j in range(0, count):
                temp = Grid([(self._lon_min + i * lon_step),
                             (self._lon_min + (i + 1) * lon_step),
                             (self._lat_min + j * lat_step),
                             (self._lat_min + (j + 1) * lat_step)])
                result.append(temp)
        return result

    def get_range(self):
        return [self._lon_min, self._lon_max, self._lat_min, self._lat_max]


class GridManager():
    def __init__(self, lonlat, min_area=1e6, split_count=2):
        self._q = Queue.Queue()
        root_grid = Grid(lonlat)
        self._q.put(root_grid)
        self._total_area = root_grid.area()
        self._min_area = min_area
        self._split_count = split_count
        self._result = {}
        self._scanned_area = 0

    def run(self):
        while not self._q.empty():
            grid = self._q.get()
            if not grid.empty():
                if grid.area() > self._min_area:
                    for item in grid.split(count=self._split_count):
                        self._q.put(item)
                else:
                    temp = grid.get_rooms()
                    for k in temp.keys():
                        self._result[k] = temp[k]
                    self._scanned_area += grid.area()
                    self._print_progress()
            else:
                self._scanned_area += grid.area()
                self._print_progress()
        return self._result

    def _print_progress(self):
        print("%d / %d = %.2f%% : %d" % (
            self._scanned_area, self._total_area, float(self._scanned_area) / self._total_area * 100,
            len(self._result.keys())))


def parse_room(json_obj):
    return (json_obj["longitude"], json_obj["latitude"])


if __name__ == '__main__':
    grid_range = [115.7, 117.4, 39.4, 41.6]  # 北京市范围，扫描别的城市，只要修改经纬度范围即可 参数格式["lon_min,lon_max,lat_min,lat_max"]

    gm = GridManager(grid_range)
    result = gm.run()
    rooms = filter(lambda x: x["room_status"] != "ycz" and x["room_status"] != "yxd", result.values())
    share_rooms = filter(lambda x: x["is_whole"] == 0, rooms)
    whole_rooms = filter(lambda x: x["is_whole"] == 1, rooms)

    print("整租房源: %d     合租房源:%d" % (len(whole_rooms), len(share_rooms)))

    f = zipfile.ZipFile('web/share_rooms.zip', 'w', zipfile.ZIP_DEFLATED)
    f.writestr('share_rooms.json', json.dumps(share_rooms))
    f.close()
    f = zipfile.ZipFile('web/whole_rooms.zip', 'w', zipfile.ZIP_DEFLATED)
    f.writestr('whole_rooms.json', json.dumps(whole_rooms))
    f.close()
