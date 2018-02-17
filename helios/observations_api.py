"""
Helios Observations API.

Methods are meant to represent the core functionality in the developer
documentation.  Some may have additional functionality for convenience.

"""
import logging
import os
from collections import namedtuple
from io import BytesIO

import numpy as np
import requests
from PIL import Image

from helios.core.mixins import SDKCore, IndexMixin, ShowMixin
from helios.core.records import ImageRecord, DataContainer
from helios.utilities import logging_utils, parsing_utils


class Observations(ShowMixin, IndexMixin, SDKCore):
    """
    The Observations API provides ground-truth data generated by the Helios
    analytics.

    """

    _core_api = 'observations'

    def __init__(self, session=None):
        """
        Initialize Observations instance.

        Args:
            session (helios.Session object, optional): An instance of the
                Session. Defaults to None. If unused a session will be
                created for you.

        """
        super(Observations, self).__init__(session=session)
        self._logger = logging.getLogger(__name__)

    def index(self, **kwargs):
        """
        Get a list of observations matching the provided spatial, text, or
        metadata filters.

        The maximum skip value is 4000. If this is reached, truncated results
        will be returned. You will need to refine your query to avoid this.

        Usage example:

        .. code-block:: python

            import helios
            obs = helios.Observations()
            state = 'Maryland'
            bbox = [-169.352,1.137,-1.690,64.008]
            sensors = 'sensors[visibility][min]=0&sensors[visibility][max]=1'
            results = obs.index(state=state,
                                bbox=bbox,
                                sensors=sensors)

        Usage example for transitions:

        .. code-block:: python

            import helios
            obs = helios.Observations()
            # transition from dry/wet to partial/fully-covered snow roads
            sensors = 'sensors[road_weather][data][min]=6&sensors[road_weather][prev][max]=3'
            results = obs.index(sensors=sensors_query)

        .. _observations_index_documentation: https://helios.earth/developers/api/observations/#index

        Args:
            **kwargs: Any keyword arguments found in the
                observations_index_documentation_.

        Returns:
             list: GeoJSON feature collections.

        """
        return super(Observations, self).index(**kwargs)

    @logging_utils.log_entrance_exit
    def preview(self, observation_ids, out_dir=None, return_image_data=False):
        """
        Get preview images from observations.

        Args:
            observation_ids (str or sequence of strs): list of observation IDs.
            out_dir (optional, str): Directory to write images to.  Defaults to
                None.
            return_image_data (optional, bool): If True images will be returned
                as numpy.ndarrays.  Defaults to False.

        Returns:
            :class:`DataContainer <helios.core.records.DataContainer>`:
            Container of :class:`ImageRecord <helios.core.records.ImageRecord>`.

        """
        if not isinstance(observation_ids, (list, tuple)):
            observation_ids = [observation_ids]

        # Create messages for worker.
        Message = namedtuple('Message', ['observation_id', 'out_dir',
                                         'return_image_data'])
        messages = [Message(x, out_dir, return_image_data) for x in observation_ids]

        # Process messages using the worker function.
        results = self._process_messages(self.__preview_worker, messages)

        return DataContainer(results)

    def __preview_worker(self, msg):
        """msg must contain observation_id and check_for_duds"""

        query_str = '{}/{}/{}/preview'.format(self._base_api_url,
                                              self._core_api,
                                              msg.observation_id)

        try:
            resp = self._request_manager.get(query_str)
        except requests.exceptions.RequestException as e:
            return ImageRecord(message=msg, query=query_str, error=e)

        # Parse key from url.
        parsed_url = parsing_utils.parse_url(resp.url)
        _, image_name = os.path.split(parsed_url.path)

        # Read image from response.
        img = Image.open(BytesIO(resp.content))

        # Write image to file.
        if msg.out_dir is not None:
            out_file = os.path.join(msg.out_dir, image_name)
            img.save(out_file)
        else:
            out_file = None

        # Read and return image data.
        if msg.return_image_data:
            img_data = np.array(img)
        else:
            img_data = None

        return ImageRecord(message=msg, query=query_str, name=image_name,
                           content=img_data, output_file=out_file)

    def show(self, observation_ids):
        """
        Get attributes for observations.

        Args:
            observation_ids (str or sequence of strs): Helios observation ID(s).

        Returns:
            :class:`DataContainer <helios.core.records.DataContainer>`:
            Container of :class:`Record <helios.core.records.Record>`.

        """
        return super(Observations, self).show(observation_ids)
