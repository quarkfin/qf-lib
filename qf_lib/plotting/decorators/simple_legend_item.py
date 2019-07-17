class SimpleLegendItem(object):
    """
        An item which can be added to a Legend in a simple way: by using its handle property. Handle is a reference
        to the matplotlib.Artist object.
    """

    def __init__(self):
        """
        Object which holds a reference to matplotlib's object which can be plotted on the chart (so called Artist).
        """
        self.legend_artist = None  # type: matplotlib.artist.Artist
