class ProgressTracer(object):
    """
    ProgressPrinter class to ease printing the progress of a particular
    long running process.

    :param totalsize: Totalsize of the whole process. This parameter
    content may change depending on the context. For example, if a file
    is being loaded total line number should be given.

    :param cb: callback to be called if the progress reached to a
     specific point. cb function is called with two parameters.
     position in the total progress and number of the total progress.

    :param cb_num: maximum number of times that callback is going to be called.
    """
    def __init__(self, totalsize, cb, cb_num=10):
        self.totalsize = totalsize
        chunksize = totalsize / cb_num
        self.progress_chunks = [i * chunksize for i in
                                range(cb_num)] if chunksize > 0 else []
        self.cb = cb
        self.cb_num = cb_num
        self.step_no = 0

    def step(self, step=None):
        self.step_no = step or self.step_no + 1
        assert isinstance(self.step_no, int)
        if len(self.progress_chunks) > 0 and self.step_no > self.progress_chunks[0]:
            self.progress_chunks = self.progress_chunks[1:]
            self.cb(self.step_no, self.totalsize)
