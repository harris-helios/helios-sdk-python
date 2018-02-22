"""
Helios Cameras API.

Methods are meant to represent the core functionality in the developer
documentation.  Some may have additional functionality for convenience.

"""
import logging

from dateutil.parser import parse

from helios.core.mixins import SDKCore, ShowMixin, ShowImageMixin, IndexMixin
from helios.core.structure import FeatureCollection
from helios.utilities import logging_utils
from helios.utilities.json_utils import merge_json


class Cameras(ShowImageMixin, ShowMixin, IndexMixin, SDKCore):
    """The Cameras API provides access to all cameras in the Helios Network."""

    _core_api = 'cameras'

    def __init__(self, session=None):
        """
        Initialize Cameras instance.

        Args:
            session (helios.Session object, optional): An instance of the
                Session. Defaults to None. If unused a session will be
                created for you.

        """
        super(Cameras, self).__init__(session=session)
        self._logger = logging.getLogger(__name__)

    @logging_utils.log_entrance_exit
    def images(self, camera_id, start_time, end_time=None, limit=500):
        """
        Get the image times available for a given camera in the media cache.

        The media cache contains all recent images archived by Helios, either
        for internal analytics or for end user recording purposes.

        Args:
            camera_id (str): Camera ID.
            start_time (str): Starting image timestamp, specified in UTC as an
                ISO 8601 string (e.g. 2014-08-01 or 2014-08-01T12:34:56.000Z).
            end_time (str, optional): Ending image timestamp, specified in UTC
                as an ISO 8601 string (e.g. 2014-08-01 or 2014-08-01T12:34:56.000Z).
            limit (int, optional): Number of images to be returned, up to a max
                of 500. Defaults to 500.

        Returns:
            sequence of strs: Image times.

        """
        if end_time:
            end = parse(end_time).utctimetuple()
        else:
            end = None

        image_times = []
        while True:
            query_str = '{}/{}/{}/images?time={}&limit={}'.format(self._base_api_url,
                                                                  self._core_api,
                                                                  camera_id,
                                                                  start_time,
                                                                  limit)
            # Get image times available.
            resp = self._request_manager.get(query_str)
            times = resp.json()['times']

            # Return now if no end_time was provided.
            if end_time is None:
                image_times.extend(times)
                break

            # Parse the last time and break if no times were found
            try:
                last = parse(times[-1]).utctimetuple()
            except IndexError:
                break

            # the last image is still newer than the end time, keep looking
            if last < end:
                if len(times) > 1:
                    image_times.extend(times[0:-1])
                    start_time = times[-1]
                else:
                    image_times.extend(times)
                    break
            # The end time is somewhere in between.
            elif last > end:
                good_times = [x for x in times if parse(x).utctimetuple() < end]
                image_times.extend(good_times)
                break
            else:
                image_times.extend(times)
                break

        if not image_times:
            self._logger.warning('No images were found for %s in the %s to %s range.',
                                 camera_id, start_time, end_time)

        return image_times

    def index(self, **kwargs):
        """
        Get a list of cameras matching the provided spatial, text, or
        metadata filters.

        The maximum skip value is 4000. If this is reached, truncated results
        will be returned. You will need to refine your query to avoid this.

        .. _cameras_index_documentation: https://helios.earth/developers/api/cameras/#index

        Args:
            **kwargs: Any keyword arguments found in the cameras_index_documentation_.

        Returns:
             list: GeoJSON feature collections.

        """
        return CamerasIndex(super(Cameras, self).index(**kwargs))

    def show(self, camera_ids):
        """
        Get attributes for cameras.

        Args:
            camera_ids (str or sequence of strs): Helios camera ID(s).

        Returns:
            :class:`DataContainer <helios.core.records.DataContainer>`:
            Container of :class:`Record <helios.core.records.Record>` instances.

        """
        return super(Cameras, self).show(camera_ids)

    def show_image(self, camera_id, times, out_dir=None, return_image_data=False):
        """
        Get images from the media cache.

        The media cache contains all recent images archived by Helios, either
        for internal analytics or for end user recording purposes.

        Args:
            camera_id (str): Camera ID.
            times (str or sequence of strs): Image times, specified in UTC as
                an ISO 8601 string (e.g. 2017-08-01 or 2017-08-01T12:34:56.000Z).
                The image with the closest matching timestamp will be returned.
            out_dir (optional, str): Directory to write images to.  Defaults to
                None.
            return_image_data (optional, bool): If True images will be returned
                as numpy.ndarrays.  Defaults to False.

        Returns:
            :class:`DataContainer <helios.core.records.DataContainer>`:
            Container of :class:`ImageRecord <helios.core.records.ImageRecord>`
            instances.

        """
        return super(Cameras, self).show_image(camera_id, times, out_dir=out_dir,
                                               return_image_data=return_image_data)


class CamerasIndex(FeatureCollection):
    """Index results for the Cameras API."""

    def __init__(self, geojson):
        super(CamerasIndex, self).__init__()

        self.raw = geojson

        self.features = None
        self.id = None
        self.city = None
        self.state = None
        self.country = None
        self.description = None
        self.provider = None

        self._get_features()
        self._build()

    def _get_features(self):
        # Combine all features into a list.
        self.features = []
        for x in self.raw:
            self.features.extend(x['features'])

    def _build(self):
        self.id = merge_json(self.features, 'id')
        self.city = merge_json(self.features, ['properties', 'city'])
        self.state = merge_json(self.features, ['properties', 'state'])
        self.country = merge_json(self.features, ['properties', 'country'])
        self.description = merge_json(self.features, ['properties', 'description'])
        self.provider = merge_json(self.features, ['properties', 'provider'])
