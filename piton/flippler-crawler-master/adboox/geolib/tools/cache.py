import pickle


class Cache(object):

    def __init__(self, name):
        self.name = name

    def _tmp_file_name(self):
        return '/tmp/' + self.name + '.cache'

    def make_new(self):
        raise NotImplementedError

    def _open(self):
        try:
            with open(self._tmp_file_name(), mode='r') as f:
                obj = pickle.load(f)
            return obj
        except Exception:
            pass

    def _save(self, obj):
        with open(self._tmp_file_name(), mode='w') as f:
            pickle.dump(obj, f, protocol=-1)

    def get(self):
        obj = self._open()
        if obj:
            return obj

        obj = self.make_new()
        self._save(obj)
        return obj
