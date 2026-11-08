'''
Author: LiQiang
Date: 2024-02-24 03:04:52
LastEditors: LiQiang
LastEditTime: 2026-11-08 11:33:48
Description: 文件描述
'''
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class DoubanmoviePipeline:
    def process_item(self, item, spider):
        print("电影排名：", item['rank'][0], "电影名称：", item['title'][0])
        return item
