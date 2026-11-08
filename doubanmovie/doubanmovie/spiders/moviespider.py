# -*- coding: utf-8 -*-
import scrapy
#导入items.py中的DoubanmovieItem类
from doubanmovie.items import DoubanmovieItem #导入item.py中的DoubanmovieItem类



class MoviespiderSpider(scrapy.Spider):
    name = 'moviespider'
    allowed_domains = ['douban.com']
    start_urls = ['http://movie.douban.com/top250']#设置爬虫程序访问的网址

    def parse(self, response):
        #获取当前页面所有<divclass="item"></div>
        movie_items=response.xpath('//div[@class="item"]')
        #循环遍历每一个电影代码块，解析每一个电影的排，名称//*[@id="content"]/div/div[1]/ol/li[1]/div/div[1]/em
        for item in movie_items:
            #创建一个空的DoubanmovieItem对象
            movie=DoubanmovieItem()
            #为对象中的属性赋值
            movie['rank']=item.xpath('div[@class="pic"]/em/text()').extract()
            #title电影名称
            movie['title']=item.xpath('div[@class="info"]/div[@class="hd"]/a/span[@class="title"][1]/text()').extract()
            #将生成好的电影采集数据对象添加到生成器中
            yield movie
            pass
        #自动请求翻页实现爬虫的深度采集
        nextPage=response.xpath('//span[@class="next"]/a/@href')
        #判断nextPage是否有效
        if nextPage:
            #拼接下一页的地址
            url=response.urljoin(nextPage[0].extract())
            #发送url后页请求
            yield scrapy.Request(url,self.parse)

        pass
