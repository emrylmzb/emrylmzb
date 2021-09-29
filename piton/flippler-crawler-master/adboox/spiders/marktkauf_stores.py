from adboox.spiders.edeka_stores import EdekaStoresSpider

class MartkaufStoresSpider(EdekaStoresSpider):
    name = '35-stores'

    def supported_store(self, store_data):
        return self.is_distributed_by(store_data, 'marktkauf')
