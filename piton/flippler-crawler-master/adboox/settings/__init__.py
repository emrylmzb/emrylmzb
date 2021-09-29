from adboox.settings.prod import *

try:
    from adboox.settings.dev import *
except ImportError:
    pass

try:
    from local_settings import *
except ImportError:
    pass
