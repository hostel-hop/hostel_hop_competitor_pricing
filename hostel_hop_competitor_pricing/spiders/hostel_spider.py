import datetime
import scrapy
from ..items import HostelItem
import json
import logging
from bs4 import BeautifulSoup

## RUN 
# scrapy crawl hostel_spider


## OUTPUT
## if saving output to the cloud you need to run this command to authenticate with gcloud
# gcloud auth application-default login
class HostelSpider(scrapy.Spider):
    name = 'hostel_spider'
    ## Comment this if you want to get result locally
    # custom_settings = {
    #     "FEEDS": {
    #         "gs://hostel-hop-storage/scraping/competitor-pricings/%(time)s.json": {
    #             "format": "json"
    #         }
    #     },
    # }
    
    def start_requests(self):
        urls = self.read_urls('matched_urls.txt')
        ## only use first 5 urls
        urls = urls[:6]

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
        for i in range(5):
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

            ## the selector should have a parent element with the id searchDateModal
            ## a parent element with the class modal-content
            ## the element should have a class that has the value "toMonth"
            ## a time attribute with the value of the date in milliseconds

             # Locate the elements that match the selector
            await page.click(selector=f'#searchDateModal .modal-content [time="{date_milliseconds}"][class~="toMonth"]')

             ## click on the second date
            await page.click(selector=f'#searchDateModal .modal-content [time="{date_milliseconds + 86400000}"][class~="toMonth"]')

            await page.wait_for_selector(selector='body.hostel-page:not(.modal-open)')

            ## wait for the page to load
            await page.wait_for_selector('#bookingSearchResult')

            booking_search_result = response.css('#bookingSearchResult')

            if not booking_search_result:
                logging.error('Could not find booking search result for date:', date_str)
                continue

            ## wait for the booking search result to load, ensure that it does not have a class
            await page.wait_for_selector('#bookingSearchResult:not(.bookingWait)')

            await page.wait_for_timeout(5000)

            ## extract the html content of the booking search result
            html_content = await page.content()

            soup = BeautifulSoup(html_content, 'html.parser')
            
            ## all room containers have a child div with the class no-last-bb
            room_containers = []

            for dorm_container in soup.find_all('div'):
                if dorm_container.find('div', class_='no-last-bb'):
                    room_containers.append({"container": dorm_container, "type": "dorm"})
                
            ## click on the label with for="radioprivate" to select the private room

            await page.click(selector='label[for="radioprivate"]')

            await page.wait_for_selector('#bookingSearchResult:not(.bookingWait)')

            await page.wait_for_timeout(5000)

            for private_container in soup.find_all('div'):
                if private_container.find('div', class_='no-last-bb'):
                    room_containers.append({"container": private_container, "type": "private"})
            
            if not room_containers:
                ## convert the date to a string
                print('No rooms found for date:', date_str)
                continue
            
           
            for container in room_containers:
                room = container.get('container')
                prices = []
                
                # Extract room title
                title_tag = room.find('h4', class_='tx-body cl-text font-weight-600')
                if title_tag:
                    room_name = title_tag.text.strip()
                else:
                    print('No room name found')
                    continue

                print('Room:', room_name)

               ## source_container = room.css('div.no-last-bb')
                source_container = room.find('div', class_='no-last-bb')

                if not source_container:
                    print('No sources found for room:', room_name)
                    continue

                source_container_anchors = source_container.find_all('a')

                print('Source containers:', source_container_anchors)

                for source_anchor in source_container_anchors:
                    booking_site = source_anchor.get('for')

                    price = source_anchor.find('span', class_='cl-text font-weight-600').text
                    price = price.strip() if price else 'Price not available'

                    ## extract currency (should be first element of the price)
                    ## example $10.00
                    currency_symbol = price[0]
                    price = price[1:]

                    prices.append({
                        'source': booking_site,
                        'price': price,
                        'currency_symbol': currency_symbol,
                        'date': date_str,
                        'room_type': room.get('type')
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
        
        ## click dorm room button
        await page.click(selector='label[for="radiodorm"]')

        await page.wait_for_selector('#bookingSearchResult:not(.bookingWait)')


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
    