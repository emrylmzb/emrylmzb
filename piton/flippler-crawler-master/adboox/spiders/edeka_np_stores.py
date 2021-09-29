from adboox.spiders.edeka_stores import EdekaStoresSpider

class EdekaNpStoresSpider(EdekaStoresSpider):
    name = '143-stores'

    def supported_store(self, store_data):
        return self.is_distributed_by(store_data, 'andere') and self.is_np(store_data)

    def is_np(self, store_data):
        name = store_data['name'].lower()
        return name.startswith('np-markt')
