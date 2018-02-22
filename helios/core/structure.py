"""Data structures for the SDK."""
import abc

import six

from helios.utilities.json_utils import merge_json


@six.add_metaclass(abc.ABCMeta)
class FeatureCollection(object):
    """
    Abstract base class for feature results.

    Features can be from GeoJSON feature collections or generic feature
    results.

    """

    def __init__(self, data):
        self.raw = data
        self._combine_features()

    @abc.abstractmethod
    def _combine_features(self):
        """
        _combine_features must be implemented in children.

        For GeoJSON all 'feature' sections will be merged and for Collections
        index results, 'results' will be merged.

        """
        self.features = []

    def _merge(self, keys):
        return merge_json(self.features, keys)

    def __delitem__(self, index):
        del self.features[index]

    def __getitem__(self, item):
        return self.features[item]

    def __iter__(self):
        self._idx = 0
        return self

    def __len__(self):
        return len(self.features)

    def __next__(self):
        if self._idx >= self.__len__():
            self._idx = 0
            raise StopIteration
        temp = self.features[self._idx]
        self._idx += 1
        return temp

    next = __next__  # For Python 2


class DataContainer(object):
    """Container for batch jobs."""

    def __init__(self, records):
        self._raw_data = records

    @property
    def failed(self):
        """Retrieve raw failed queries."""
        return [x for x in self._raw_data if not x.ok]

    @property
    def succeeded(self):
        """Retrieve raw successful queries."""
        return [x for x in self._raw_data if x.ok]

    @property
    def results(self):
        """Retrieve content from successful queries."""
        return [x.content for x in self._raw_data if x.ok]

    def __contains__(self, item):
        return item in self._raw_data

    def __delitem__(self, index):
        del self._raw_data[index]

    def __getattr__(self, item):
        """
        Retrieve combined attributes from all records in container.

        .. code-block:: python

            #data is an instance of DataContainer and contains Record instances.
            all_messages = data.message  # Messages are what is sent to processing pools and contain input parameters, etc.
            all_queries = data.query
            all_content = data.content  # Will be None or data, depending on errors.
            all_errors = data.errors  # Will be None or an exception.

        """
        return [getattr(x, item) for x in self._raw_data]

    def __getitem__(self, item):
        return self._raw_data[item]

    def __iter__(self):
        self._idx = 0
        return self

    def __len__(self):
        return len(self._raw_data)

    def __next__(self):
        if self._idx >= self.__len__():
            self._idx = 0
            raise StopIteration
        temp = self._raw_data[self._idx]
        self._idx += 1
        return temp

    def __setitem__(self, index, value):
        self._raw_data[index] = value

    next = __next__  # For Python 2


class Record(object):
    """
    Record class for general use.

    Args:
        message (tuple): Original message. This will be a namedtuple containing
            all the inputs for an individual call within a batch job.
        query (str): API query.
        content: Returned content. To be defined by method.
        error (exception): Exception that occurred, if any.

    """

    def __init__(self, message=None, query=None, content=None, error=None):
        self.message = message
        self.query = query
        self.content = content
        self.error = error

    @property
    def ok(self):
        """
        Check if failure occurred.

        Returns:
            bool: False if error occurred, and True otherwise.

        """
        if self.error:
            return False
        return True


class ImageRecord(Record):
    """
    Record class for images.

    Args:
        message (tuple): Original message. This will be a namedtuple containing
            all the inputs for an individual call within a batch job.
        query (str): API query.
        content (numpy.ndarray): Image as a Numpy ndarray.
        error (exception): Exception that occurred, if any.
        name (str): Name of image.
        output_file (str): Full path to image file that was written.

    """

    def __init__(self, message=None, query=None, content=None, error=None,
                 name=None, output_file=None):
        super(ImageRecord, self).__init__(message=message, query=query,
                                          content=content, error=error)
        self.name = name
        self.output_file = output_file
