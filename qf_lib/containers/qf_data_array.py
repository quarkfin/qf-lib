import xarray as xr


class QFDataArray(xr.DataArray):
    DATES = "dates"
    TICKERS = "tickers"
    FIELDS = "fields"

    def __setattr__(self, name, value):
        # Makes it possible to set indices in this way: qf_data_array.fields = ["OPEN", "CLOSE"].
        # Otherwise one would need to set them like this: qf_data_array[QFDataArray.FIELDS] = ["OPEN", "CLOSE"]
        # if name == self.TICKERS or name == self.DATES or name == self.FIELDS:
        if name in [self.FIELDS, self.TICKERS, self.DATES]:
            self.__setitem__(name, value)
        else:
            super().__setattr__(name, value)

    @classmethod
    def create(cls, data, dates, tickers, fields, name=None):
        """
        Helper method for creating a QFDataArray. __init__() methods can't be used for that, because its signature
        must be the same as the signature of xr.DataArray.__init__().

        Parameters
        ----------
        data
            data that should be put in the array (it's dimensions must be in the proper order: dates, tickers, fields).
        dates
            dates index (labels)
        tickers
            tickers index (labels)
        fields
            fields index (labels)
        name
            name of the QFDataArray

        Returns
        -------
        QFDataArray
        """
        coordinates = {cls.DATES: dates, cls.TICKERS: tickers, cls.FIELDS: fields}
        dimensions = (cls.DATES, cls.TICKERS, cls.FIELDS)
        return QFDataArray(data, coordinates, dimensions, name)

    @classmethod
    def from_xr_data_array(cls, xr_data_array: xr.DataArray):
        """
        Converts regular xr.DataArray into QFDataArray.

        Parameters
        ----------
        xr_data_array
            xr.DataArray with 3 dimensions: dates, tickers and fields.

        Returns
        -------
        QFDataArray
        """
        xr_data_array = xr_data_array.transpose(cls.DATES, cls.TICKERS, cls.FIELDS)
        qf_data_array = QFDataArray.create(xr_data_array.data, xr_data_array.dates, xr_data_array.tickers,
                                           xr_data_array.fields, xr_data_array.name)
        return qf_data_array

    @classmethod
    def concat(cls, objs, dim=None, data_vars='all', coords='different', compat='equals', positions=None,
               indexers=None, mode=None, concat_over=None):
        """
        Concatenates different xr.DataArrays and then converts the result to QFDataArray.

        See Also
        --------
        docstring for xr.concat()
        """
        result = xr.concat(
            objs, dim, data_vars, coords, compat,positions, indexers, mode, concat_over
        )  # type: xr.DataArray
        result = QFDataArray.from_xr_data_array(result)

        return result
