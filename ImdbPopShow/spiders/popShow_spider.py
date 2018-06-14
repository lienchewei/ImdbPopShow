import scrapy
from ImdbPopShow import ImdbpopshowItem


main_url = 'http://www.imdb.com'

class ImdbPopShowSpider(scrapy.Spider):

    name = "imdbPopShowSpider"
    start_urls = ['http://www.imdb.com/chart/tvmeter?ref_=nv_tvv_mptv_4']

    def parse(self, response):
        
        pat = re.compile('http://www.imdb.com\/title\/t{2}\d+\/')
        tbdy_list = response.xpath('//tbody[@class="lister-list"]/tr')
        for tr in tbdy_list:
            href = tr.xpath('td[@class="titleColumn"]/a/@href').extract_first()
            result = pat.match(main_url + href)
            url = result.group()
            yield scrapy.Request(url=url, callback=self.parse_tvshow_metadata)

    def parse_show_metadata(self, response):

        show = ImdbpopshowItem()

        show['link'] = response.url
        try:
            show['title'] = response.xpath('//h1[@itemprop="name"]/text()').extract_first().strip()
        except (TypeError, AttributeError):
            show['title'] = None
        try:
            show['rate'] = response.xpath('//span[@itemprop="ratingValue"]/text()').extract_first()
        except (TypeError, AttributeError):
            show['rate'] = None
        try:
            show['duration'] = response.xpath('//time[@itemprop="duration"]/text()').extract_first().strip()
        except (TypeError, AttributeError):
            show['duration'] = None
        try:
            show['stars'] = response.xpath('//span[@itemprop="actors"]/a/span/text()').extract()
        except (TypeError, AttributeError):
            show['stars'] = None
        try:
            show['creators'] = response.xpath('//span[@itemprop="creator"]/a/span/text()').extract()
        except (TypeError, AttributeError):
            show['creators'] = None
        try:
            show['photos'] = [main_url+href for href in response.xpath('//div[@class="mediastrip"]/a/@href').extract()]
        except (TypeError, AttributeError):
            show['photos'] = None
        try:
            show['actors'] = response.xpath('//td[@itemprop="actor"]/a/span/text()').extract()
        except (TypeError, AttributeError):
            show['actors'] = None
        try:
            show['storyline'] = response.xpath('//div[@class="inline canwrap"]/p/text()').extract_first().strip()
        except (TypeError, AttributeError):
            show['storyline'] = None
        try:
            show['genres'] = [value.strip() for value in response.xpath('//div[@itemprop="genre"]/a/text()').extract()]
        except (TypeError, AttributeError):
            show['genres'] = None
        
        try:
            seasons = response.xpath('//div[@class="seasons-and-year-nav"]/div[3]/a/@href').extract_first()
            season_list = []
            for i in range(seasons):
                season_link = response.url + 'episodes?season=' + str(i+1)
                season_request = scrapy.Request(url=season_link, callback=self.parse_show_season)
                yield season_request
                season_list.append(season_request)
            show['seasons'] = season_list
        except (TypeError, AttributeError):
            pass

        div_txt_block = response.xpath('//div[@id="titleDetails"]/div[@class="txt-block"]')
        for div in div_txt_block:
            h4_text = div.xpath('.//h4/text()').extract_first()
            if h4_text == 'Country:':
                try:
                    show['country'] = div.xpath('.//a/text()').extract()
                except (TypeError, AttributeError):
                    show['country'] = None
            elif h4_text == 'Language:':
                try:
                    show['language'] = div.xpath('.//a/text()').extract()
                except (TypeError, AttributeError):
                    show['language'] = None
            elif h4_text == 'Release Date:':
                rel_date_href = div.xpath('.//span[@class="see-more inline"]/a/@href').extract_first()
                rel_date_link = response.url + rel_date_href
                request = scrapy.Request(url=rel_date_link, callback=self.parse_show_reledate)
                request.meta['show'] = show
                yield request
            elif h4_text == 'Production Co:':
                company_href = div.xpath('.//span[@class="see-more inline"]/a/@href').extract_first()
                company_link = response.url + company_href
                request = scrapy.Request(url=company_link, callback=self.parse_show_company)
                request.meta['show'] = show
                yield request
    
    def parse_show_reledate(self, response):

        show = response.meta['show']

        trs = response.xpath('//table[@id="release_dates"]/tr')
        rel_date_list = []
        for tr in trs:
            rel_date_dict = {}
            rel_date_dict['country'] = tr.xpath('.//a/text()').extract_first()
            rel_date_dict['date'] = tr.xpath('.//td[@class="release_date"]/text()').extract_first()
            rel_date_list.append(rel_date_dict)
        try:
            show['releaseDate'] = rel_date_list
        except (TypeError, AttributeError):
            show['releaseDate'] = None

    def parse_show_company(self, response):

        show = response.meta['show']
        try:
            show['production'] = response.xpath(
                '(//div[@id="company_credits_content"]/ul[@class="simpleList"])[1]/li/a/text()').extract()
        except (TypeError, AttributeError):
            show['production'] = None
        li_text = response.xpath('(//div[@id="company_credits_content"]/ul[@class="simpleList"])[2]/li')
        try:
            show['distributor'] = [i.strip().replace(' ', '') for i in li_text.xpath('string(.)').extract()]
        except (TypeError, AttributeError):
            show['distributor'] = None
        yield show

    def parse_show_season(self, response):
        return response.xpath('//h3[@id="episode_top"]/text()').extract_first()