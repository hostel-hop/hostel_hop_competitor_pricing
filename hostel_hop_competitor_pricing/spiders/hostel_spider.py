import datetime
import scrapy
from ..items import HostelItem
import json
import logging
from scrapy_selenium import SeleniumRequest
from scrapy_playwright.page import PageMethod

# scrapy crawl hostel_spider
class HostelSpider(scrapy.Spider):
    name = 'hostel_spider'
    
    def start_requests(self):
        urls = self.read_urls('matched_urls.txt')
        ## only use first 5 urls
        urls = urls[:1]

        for url in urls:
           yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "errback": self.errback
                }
            )
    
    def read_urls(self, file_path):
        with open(file_path, 'r') as file:
            urls = file.read().splitlines()
        return urls
    
    async def parse(self, response):
        item = HostelItem()
        item['property_hostelz_url'] = response.url
        item['property_name'] = response.css('h1::text').get().strip()

        rooms = []

        print('----------------------')
        print(item['property_name'])

        page = response.meta["playwright_page"]

        ## create list of dates spanning the next 30 days sdtarting from now
      
        now = datetime.datetime.now()
        ## remove the time part
        now = datetime.datetime(now.year, now.month, now.day)
        dates = []
        for i in range(3):
            date = now + datetime.timedelta(days=i)
            dates.append(date)


        for date in dates:
            date_str = date.strftime('%Y-%m-%d')
            date_milliseconds = date.timestamp() * 1000

            ## remove any decimal points
            date_milliseconds = int(date_milliseconds)
            ## click on the date picker
            await page.click(selector='#searchDateContent')

            ## click on the the current date as first and next date as second
            ## the first date will be the current date
            ## the second date will be the next date
         
            ## selct the dates based on the time attirbute  example: time=1729144800000
            ## this will be the time in milliseconds
            ## click on the first date

            await page.click(selector=f'#searchDateModal [time="{date_milliseconds}"]')  # First date

            ## click on the second date
            await page.click(selector=f'#searchDateModal [time="{date_milliseconds + 86400000}"]')
            
            ## wait for the page to load
            await page.wait_for_selector('#bookingSearchResult')

            booking_search_result = response.css('#bookingSearchResult')

            if not booking_search_result:
                logging.error('Could not find booking search result for date:', date_str)
                continue

            ## take screenshot of the page ans save it
            ##await page.screenshot(path=f'./screenshots/{item['property_name']}/{date_str}.png')
             ## wait 5 seconds for the page to load
            await page.wait_for_timeout(4000)
            
            room_containers = response.css('.mb-5.mb-lg-6')

            print('Room containers:', len(room_containers))

            if not room_containers:
                ## convert the date to a string
                print('No rooms found for date:', date_str)
                continue
            
           
            for room in room_containers:
                prices = []
                # Extract room name
                room_name = room.css('h4.tx-body.cl-text.font-weight-600::text').get().strip()
    
                source_container = room.css('div.no-last-bb')

                for source in source_container.css('a'):
                    booking_site = source.attrib['for']

                    price = source.css('.cl-text.font-weight-600::text').get()
                    price = price.strip() if price else 'Price not available'

                    ## extract currency (should be first element of the price)
                    ## example $10.00
                    currency_symbol = price[0]
                    price = price[1:]

                    prices.append({
                        'source': booking_site,
                        'price': price,
                        'currency_symbol': currency_symbol,
                        'date': date_str
                    })

                ## if room already exists, append the price to the room
                ## otherwise create a new room

                existing_room = next((r for r in rooms if r['name'] == room_name), None)
                if existing_room:
                    existing_room['prices'].append(prices)
                else:
                    room = {
                        'name': room_name,
                        'prices': prices,
                    }
                    rooms.append(room)

            item['rooms'] = rooms

        yield item
    
    async def errback(self, failure):
        page = failure.request.meta["playwright_page"]
        await page.close()

    def log_network_requests(self, response):
        network_requests = response.css('script::text').re(r'fetch\("([^"]+)"\)')
        for request in network_requests:
            logging.info(f"Detected network request: {request}")
            self.analyze_dynamic_data(request)

    def analyze_dynamic_data(self, url):
        try:
            response = scrapy.Request(url=url)
            data = json.loads(response.text)
            logging.info(f"Dynamic data: {data}")
        except Exception as e:
            logging.error(f"Failed to retrieve dynamic data from {url}: {e}")
    