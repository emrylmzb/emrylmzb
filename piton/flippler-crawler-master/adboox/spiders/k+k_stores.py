import re
import logging
import scrapy
from adboox.items import StoreLoader
from adboox.utils import calendar
from adboox.utils import load_csv_data
from adboox.spiders.base import BaseAdbooxSpider
from adboox.mixins.store import SendStoresWhenIdleMixin

logger = logging.getLogger(__name__)

class StoreSpider(SendStoresWhenIdleMixin, BaseAdbooxSpider):
    name = "925-stores"
    start_urls = ["https://www.klaas-und-kock.de/angebote/unsere-angebote/"]

    def parse(self, response):
        data = {"postcode": "", "radius": "50"}
        zipcodes = [city['PostalCode'] for city in load_csv_data('de_cities.csv')]
        for zipcode in zipcodes:
            data["postcode"] = zipcode
            yield scrapy.FormRequest(url="https://www.klaas-und-kock.de/angebote/unsere-angebote/", formdata=data,
                                     callback=self.parse_stores)

    def parse_stores(self, response):
        for store in response.css('div.col-md-6 > :first-child'):
            store_texts = [text.strip() for text in store.xpath("descendant-or-self::text()").extract()]
            telephone = re.sub(r'^\D+', '', store_texts[8])
            if telephone not in self.stores:
                zipcode_and_city = store_texts[6].partition(" ")
                address_line1 = store_texts[4]
                address_line2 = store_texts[5]

                if zipcode_and_city[0] == "(Anfahrtsskizze)":
                    address = address_line1
                    zipcode_and_city = store_texts[5].partition(" ")
                    work_hours = store_texts[10]
                    telephone = store_texts[7]
                else:
                    address = ("{} {}".format(address_line1, address_line2))
                    work_hours = store_texts[11]
                day_hours = work_hours.split(" ")
                gmaps_url = store.css("a::attr(href)").get()
                lat, lon = gmaps_url.split("!3d")[1].split("!4d")

                try:
                    store_open, store_close = day_hours[3].split("-")
                except:
                    store_open, store_close = day_hours[3], day_hours[5]

                sl = StoreLoader(selector=store, response=response)
                sl.add_css("Name", "strong::text")
                sl.add_value("Address", address)
                sl.add_value("PostCode", zipcode_and_city[0])
                sl.add_value("City", zipcode_and_city[2])
                sl.add_value("PhoneNumber", telephone)
                sl.add_value("OpeningDays", work_hours)
                item = sl.load_item()
                item['GeoLocation'] = {"Lat": lat, "Lon": lon}

                for _, day in calendar.iter_from_abbr_de(day_hours[0].lower(), day_hours[2].lower()):
                    item[day] = {"Open": store_open, "Close": store_close}
                self.stores[item['PhoneNumber']] = item
                yield item
