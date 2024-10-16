import datetime
import scrapy
from ..items import HostelItem
import json
import logging

## RUN 
# scrapy crawl hostel_spider


## OUTPUT
## if saving output to the cloud you need to run this command to authenticate with gcloud
# gcloud auth application-default login
class HostelSpider(scrapy.Spider):
    name = 'hostel_spider'
 
    
    def __init__(self, bucket_name='hostel-hop-storage', start_date=None, end_date=None, url_count=None, use_google_storage=False, debug=False, *args, **kwargs):
        super(HostelSpider, self).__init__(*args, **kwargs)
        self.bucket_name = bucket_name
        self.start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
        self.end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d') if end_date else None
        self.url_count = int(url_count) if url_count else None

        if use_google_storage and self.start_date and self.end_date:
            ## use start date and end date to create a folder name
            ## example gs url: gs://hostel-hop-storage/scraping/competitor-pricings/2024_10_11-2024_10_15/
            self.custom_settings = {
                "FEEDS": {
                    f"gs://{self.bucket_name}/scraping/competitor-pricings/{self.start_date.strftime('%Y_%m_%d')}-{self.end_date.strftime('%Y_%m_%d')}/": {
                        "format": "json"
                    }
                },
            }
        self.debug = debug
   

    def start_requests(self):
        items = self.read_urls('hostelz_search_results.json')
        ## only use first 5 urls
        items = items[:self.url_count] if self.url_count else items

       

        for item in items:
            if item.get('similarity_score', 0) < 70:
                continue;

            yield scrapy.Request(
                url=item.get('property_hostelz_url'),
                callback=self.parse,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "errback": self.errback,
                    "hostel_hop_property_id": item.get('hostel_hop_property_id')
                }
            )
    
    def read_urls(self, file_path):
        with open(file_path, 'r') as file:
            items = json.load(file)
        return items
    
    async def parse(self, response):
        try:
            item = HostelItem()
            item['property_hostelz_url'] = response.url
            item['property_name'] = response.css('h1::text').get().strip()
            item['hostel_hop_property_id'] = response.meta.get('hostel_hop_property_id')

            rooms = []

            print('----------------------')
            print(item['property_name'])

            page = response.meta["playwright_page"]

            ## if a button with  skip dates  is present, click on it
            try:
                modal_open = await page.wait_for_selector(selector='body.modal-open')
            except Exception as e:
                modal_open = None

            ## modal open 
            if modal_open:
                await page.click('button:has-text("skip dates")');
                await page.wait_for_selector(selector='body:not(.modal-open)')

            ## create list of dates based on input date range or default to next 5 days
            if self.start_date and self.end_date:
                dates = [self.start_date + datetime.timedelta(days=i) for i in range((self.end_date - self.start_date).days + 1)]
            else:
                now = datetime.datetime.now()
                now = datetime.datetime(now.year, now.month, now.day)
                dates = [now + datetime.timedelta(days=i) for i in range(5)]

            for date in dates:
                date_str = date.strftime('%Y-%m-%d')
                date_milliseconds = int(date.timestamp() * 1000)

                ## remove any decimal points
                date_milliseconds = int(date_milliseconds)

                ## class="compare-prices-tab"
                await page.click(selector='.compare-prices-tab')


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
                ## id="2024-10-11"
                ## class="dp__calendar_item"

                ## click class="compare-prices-tab-control-panel-text tx-small"
                await page.click(selector='.compare-prices-tab-control-panel-text.tx-small')

                next_date = (date + datetime.timedelta(days=1)).strftime('%Y-%m-%d')

                try:
                    await page.click(f'[id="{date_str}"]')
                except Exception as e:
                    print('error clicking date', date_str)
                    continue

                try:
                    await page.click(f'[id="{next_date}"]')
                except Exception as e:
                    print('error clicking date', next_date)
                    continue

            
                await page.wait_for_selector(selector='body:not(.modal-open)')

                ## wait for https://www.hostelz.com/listing-booking-search/226874 to load
                ##async with page.expect_response(lambda response: response.url == "https://example.com" and response.status == 200 and response.request.method == "get") as response_info:
                room_containers = []

                ## ensure requpayload.roomType
                ## handle timeout gracefully    
                try:
                    async with page.expect_response(lambda response: '/listing-booking-search' in response.url and response.status == 200) as dorm_response_info:
                        dorm_response = await dorm_response_info.value
                except Exception as e:
                    dorm_response = None

                if dorm_response:
                    dorm_json = await dorm_response.json() 

                if self.debug:
                    print('dorm_json', dorm_json)   

                if dorm_json:
                    for room in dorm_json:
                        if room.get('primary').get('roomType') == 'dorm':
                            room_containers.append({"container": room, "type": "dorm"})

                ## click on the label with for="hz-switcher-private" to select the private room
                await page.click(selector='label[for="hz-switcher-private"]')

                ## ensure the response is for the private rooms and not the same as the dorms
                ## handle timeout gracefully    
                try:
                    async with page.expect_response(lambda response: '/listing-booking-search' in response.url and response.status == 200) as private_response_info:
                        private_response = await private_response_info.value
                except Exception as e:
                    private_response = None
                
                if private_response:
                    private_json = await private_response.json() 

                if self.debug:
                    print('private_json', private_json)

                if private_json:
                    for room in private_json:
                        if room.get('primary').get('roomType') == 'private':
                            room_containers.append({"container": room, "type": "private"})

                
                if not room_containers:
                    ## convert the date to a string
                    print('No rooms found for date:', date_str)
                    continue
                

                if self.debug:
                    print('room_containers', room_containers)
            
                for container in room_containers:
                    room = container.get('container')
                    prices = []
                    
                    # Extract room title
                    room_name = room.get('title')
                    if self.debug:
                        print('Room:', room_name)
                    
                    ## get primary and other prices

                    primary_price = room.get('primary')
                    other_prices = room.get('otherPrices')

                    if primary_price:

                        ## extract price and currency symbol
                        price = primary_price.get('averagePricePerBlockPerNight')
                        currency_symbol = price[0]
                        price = price[1:]
                        
                        prices.append({
                            'source': primary_price.get('otaShortName'),
                            'price': price,
                            'currency_symbol': currency_symbol,
                            
                            'room_type': container.get('type')
                        })

                    if other_prices:
                        
                        for price in other_prices:
                            ## extract price and currency symbol
                            price_value = price.get('averagePricePerBlockPerNight')
                            currency_symbol = price_value[0]
                            price_value = price_value[1:]

                            prices.append({
                                'source': price.get('otaShortName'),
                                'price': price_value,
                                'currency_symbol': currency_symbol,
                        
                                'room_type': container.get('type')
                            })
                    ## if room already exists, append the price to the room
                    ## otherwise create a new room

                    existing_room = next((r for r in rooms if r['name'] == room_name), None)
                    if existing_room:
                        existing_room['prices'][date_str] = prices
                    else:
                        room = {
                            'name': room_name,
                            'prices': {
                                date_str: prices
                            },
                        }
                        rooms.append(room)

                    
                item['rooms'] = rooms
            
                ## click dorm room button
                await page.click(selector='label[for="hz-switcher-dorm"]')


            yield item
        except Exception as e:
            print('error parsing', e)
            item['error_message'] = str(e)
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
