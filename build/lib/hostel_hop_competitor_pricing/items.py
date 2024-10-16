# items.py

import scrapy

class HostelItem(scrapy.Item):
    hostel_hop_property_id = scrapy.Field()
    property_hostelz_url = scrapy.Field()
    property_name = scrapy.Field()
    hostel_hop_property_id = scrapy.Field()
    rooms = scrapy.Field()
    error_message = scrapy.Field()


class HostelzUrlItem(scrapy.Item):
    property_hostelz_url = scrapy.Field()
    property_name = scrapy.Field()
    hostel_hop_property_id = scrapy.Field()
    error_message = scrapy.Field()