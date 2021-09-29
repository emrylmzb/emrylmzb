from adboox.spiders.edeka_stores import EdekaStoresSpider

class EdekaExpressStoresSpider(EdekaStoresSpider):
    name = '924-stores'

    def supported_store(self, store_data):
        return self.is_distributed_by(store_data, 'edeka') and self.is_express(store_data)
