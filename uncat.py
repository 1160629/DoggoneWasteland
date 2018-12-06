from threading import Thread, Event


# uncategorised things


# from https://stackoverflow.com/questions/323972/is-there-any-way-to-kill-a-thread
class StoppableThread(Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self, target=None):
        super(StoppableThread, self).__init__(target=target)
        self._stop_event = Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()
