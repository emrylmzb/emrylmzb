import os.path
from urllib.parse import urljoin
from adboox.utils.types import Resource


class DirectBrochureDownloadMixin(object):
    def gen_pdf_pathname(self, response):
        """ Let the downloaded pdf file be saved in to the fileserver path directly """
        filename = response.url.split('/')[-1]
        outfile = os.path.join(self.fileserver_path, filename)
        return outfile

    def gen_fileserver_pathname(self, gen_pathname, _):
        """ This spider saved the downloaded pdf into the fileserver directory already. """
        filename = gen_pathname.split('/')[-1]
        return urljoin(self.fileserver_url, filename)

    def create_pdf_resource(self, url, resource_key, store, meta=None):
        """ Returns true if resource is created. """
        resource = self.resources.get(resource_key)
        if resource:
            resource.stores.append(store)
            return False
        else:
            stores = [store] if store else []
            resource = Resource.from_kw(urls=[url], stores=stores, key=resource_key, type='Pdf')
            self.resources[resource_key] = resource
            return True

    def borchure_downloaded(self, response):
        resource_key = response.meta.get('resource_key')
        resource = self.resources[resource_key]
        resource.outfile = self.gen_pdf_pathname(response)
