import scrapy
from ..items import HostelItem
import json
import logging

# scrapy crawl hostel_spider
class HostelSpider(scrapy.Spider):
    name = 'hostel_spider'
    
    def start_requests(self):
        urls = self.read_urls('matched_urls.txt')
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)
    
    def read_urls(self, file_path):
        with open(file_path, 'r') as file:
            urls = file.read().splitlines()
        return urls
    
    def parse(self, response):
        item = HostelItem()
        item['property_hostelz_url'] = response.url
        item['property_name'] = response.css('h1::text').get().strip()
        item['hostel_hop_property_id'] = self.generate_property_id(response) 

        self.log_network_requests(response)
        
        rooms = []
        room_elements = response.css('.room-class')  
        for room_element in room_elements:
            room_name = room_element.css('.room-name-class::text').get().strip()
            prices = []

            price_elements = room_element.css('.price-class')  
            for price_element in price_elements:
                date = price_element.css('.date-class::text').get().strip()
                best_price = price_element.css('.price-amount-class::text').get().strip()
                prices.append({
                    'date': date,
                    'best_price': best_price
                })

            room = {
                'name': room_name,
                'hostel_hop_room_id': self.generate_room_id(room_name),  
                'prices': prices
            }
            rooms.append(room)

        item['sources'] = [
            {
                'slug': 'hostel-world',
                'rooms': rooms
            }
        ]
        
        yield item

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

    def generate_property_id(self, response):
        return hash(response.url)

    def generate_room_id(self, room_name):
        return hash(room_name)
