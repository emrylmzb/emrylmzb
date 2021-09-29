from adboox.spiders.edeka_stores import EdekaStoresSpider

class EdekaCenterStoresSpider(EdekaStoresSpider):
    name = '919-stores'

    def supported_store(self, store_data):
        return self.is_distributed_by(store_data, 'edeka') and self.is_edeka_center(store_data)
