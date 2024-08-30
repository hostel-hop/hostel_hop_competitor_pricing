# items.py

import scrapy

class HostelItem(scrapy.Item):
    property_hostelz_url = scrapy.Field()
    property_name = scrapy.Field()
    hostel_hop_property_id = scrapy.Field()
    sources = scrapy.Field()
