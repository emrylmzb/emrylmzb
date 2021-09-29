import os
import stat


def fix_permissions(path):
    """  Makes file readable for every one, writable for user only. """
    os.chmod(path, stat.S_IREAD | stat.S_IWRITE | stat.S_IXUSR | stat.S_IRGRP |
             stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)