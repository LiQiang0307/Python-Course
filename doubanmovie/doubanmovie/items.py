'''
Author: LiQiang
Date: 2024-02-24 03:04:52
LastEditors: LiQiang
LastEditTime: 2026-11-08 11:28:51
Description: 文件描述
'''
# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class DoubanmovieItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    rank = scrapy.Field() # 排名
    title = scrapy.Field() # 电影名称
    pass
