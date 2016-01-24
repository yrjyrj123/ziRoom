# ziRoom

自动搜集链家自如品牌房源，提供计算房源到指定位置距离(地球球面距离)的功能，支持多核。

## 安装依赖的模块:

	pip install -r requirements.txt

## 使用方法：

./ziRoom.py city cores thread lon lat outfile

- city:城市的拼音，目前支持shenzhen(深圳),shanghai(上海),beijing(北京)
- cores:解析HTML使用的CPU核心数
- thread:用于爬取HTML的线程数
- lon:指定地点的经度
- lat:指定地点的纬度
- outfile:爬取结果存放的位置

example: 

	./ziRoom.py 7 32 116.2933220000 40.0562850000 out.txt

PS：猜猜我在哪里