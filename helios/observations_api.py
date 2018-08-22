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
import pandas as pd
import requests
from PIL import Image
from helios.core.mixins import SDKCore, IndexMixin, ShowMixin
from helios.core.structure import ImageRecord, ImageCollection, RecordCollection
from helios.utilities import logging_utils, parsing_utils

logger = logging.getLogger(__name__)


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

    def index(self, **kwargs):
        """
        Get observations matching the provided spatial, text, or
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
             :class:`ObservationsFeatureCollection <helios.observations_api.ObservationsFeatureCollection>`

        """
        results = super(Observations, self).index(**kwargs)

        content = []
        for record in results:
            if record.ok:
                for feature in record.content['features']:
                    content.append(ObservationsFeature(feature))

        return ObservationsFeatureCollection(content, results)

    @logging_utils.log_entrance_exit
    def preview(self, observation_ids, out_dir=None, return_image_data=False):
        """
        Get preview images from observations.

        Args:
            observation_ids (str or list of strs): list of observation IDs.
            out_dir (optional, str): Directory to write images to.  Defaults to
                None.
            return_image_data (optional, bool): If True images will be returned
                as numpy.ndarrays.  Defaults to False.

        Returns:
            :class:`ImageCollection <helios.core.structure.ImageCollection>`

        """
        if not isinstance(observation_ids, (list, tuple)):
            observation_ids = [observation_ids]

        # Create messages for worker.
        Message = namedtuple('Message', ['observation_id', 'out_dir',
                                         'return_image_data'])
        messages = [Message(x, out_dir, return_image_data) for x in observation_ids]

        # Make sure directory exists.
        if out_dir:
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)

        # Process messages using the worker function.
        results = self._process_messages(self.__preview_worker, messages)

        content = []
        for record in results:
            if record.ok:
                content.append(record.content)

        return ImageCollection(content, results)

    def __preview_worker(self, msg):
        """msg must contain observation_id, out_dir, and return_image_data"""

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

        # Write image to file.
        if msg.out_dir is not None:
            out_file = os.path.join(msg.out_dir, image_name)
            with open(out_file, 'wb') as f:
                f.write(resp.content)
        else:
            out_file = None

        # Read and return image data.
        if msg.return_image_data:
            # Read image from response.
            img_data = np.asarray(Image.open(BytesIO(resp.content)))
        else:
            img_data = None

        return ImageRecord(message=msg, query=query_str, name=image_name,
                           content=img_data, output_file=out_file)

    def show(self, observation_ids):
        """
        Get attributes for observations.

        Args:
            observation_ids (str or list of strs): Helios observation ID(s).

        Returns:
            :class:`ObservationsFeatureCollection <helios.observations_api.ObservationsFeatureCollection>`

        """
        results = super(Observations, self).show(observation_ids)

        content = []
        for record in results:
            if record.ok:
                content.append(ObservationsFeature(record.content))

        return ObservationsFeatureCollection(content, results)


class ObservationsFeature(object):
    """
    Individual Observation GeoJSON feature.

    Attributes:
        city (str): 'city' value for the feature.
        country (str): 'country' value for the feature.
        description (str): 'description' value for the feature.
        id (str): 'id' value for the feature.
        json (dict): Raw JSON feature.
        prev_id (str): 'prev_id' value for the feature.
        region (str): 'region' value for the feature.
        sensors (dict): 'sensors' value for the feature.
        state (str): 'state' value for the feature.
        time (str): 'time' value for the feature.

    """

    def __init__(self, feature):
        self.json = feature

        # Use dict.get built-in to guarantee all values will be initialized.
        self.city = feature['properties'].get('city')
        self.country = feature['properties'].get('country')
        self.description = feature['properties'].get('description')
        self.id = feature.get('id')
        self.prev_id = feature['properties'].get('prev_id')
        self.region = feature['properties'].get('region')
        self.sensors = feature['properties'].get('sensors')
        self.state = feature['properties'].get('state')
        self.time = feature['properties'].get('time')


class ObservationsFeatureCollection(object):
    """
    Collection of GeoJSON features obtained via the Observations API.

    Convenience properties are available to extract values from every feature.

    Attributes:
        features (list of :class:`ObservationsFeature <helios.core.structure.ObservationsFeature>`):
            All features returned from a query.

    """

    def __init__(self, features, records=None):
        self.features = features
        self.records = RecordCollection(records=records)

    @property
    def city(self):
        """'city' values for every feature."""
        return [x.city for x in self.features]

    @property
    def country(self):
        """'country' values for every feature."""
        return [x.country for x in self.features]

    @property
    def description(self):
        """'description' values for every feature."""
        return [x.description for x in self.features]

    @property
    def id(self):
        """'id' values for every feature."""
        return [x.id for x in self.features]

    @property
    def json(self):
        """Raw 'json' for every feature."""
        return [x.json for x in self.features]

    @property
    def prev_id(self):
        """'prev_id' values for every feature."""
        return [x.prev_id for x in self.features]

    @property
    def region(self):
        """'region' values for every feature."""
        return [x.region for x in self.features]

    @property
    def sensors(self):
        """'sensors' values for every feature."""
        return [x.sensors for x in self.features]

    @property
    def state(self):
        """'state' values for every feature."""
        return [x.state for x in self.features]

    @property
    def time(self):
        """'time' values for every feature."""
        return [x.time for x in self.features]

    def sensors_to_dataframes(self, output_dir=None, prefix=None):
        """
        Combine sensor blocks and other useful feature information for
        observations into Pandas DataFrame objects.

        DataFrames will contain the time, value, previous value,
        observation ID, and previous observation ID from each feature.

        Optionally, DataFrames can be written to CSV files. These will follow
        the format of {prefix}_{sensor_name}.csv.

        Args:
            output_dir (str, optional): Output directory to write files to. If
                None, then no files will be written. Defaults to None.
            prefix (str, optional): Prefix to append to filenames. If None, no
                prefix will be prepended. Defaults to None.

        Returns:
            dict: Pandas DataFrame objects for each sensor.

        """
        data = {}
        for feature in self.features:
            for sensor, sensor_data in feature.sensors.items():
                if sensor not in data:
                    data[sensor] = []
                data[sensor].append((sensor,
                                     feature.time,
                                     sensor_data.get('data', -1),
                                     sensor_data.get('prev', -1),
                                     feature.id,
                                     feature.prev_id))

        # Establish data frames for each sensor.
        header = ['Sensor', 'Time', 'Data', 'Previous', 'ID', 'Previous_ID']
        output_data = {name: pd.DataFrame(value, columns=header).sort_values(by=['Time'])
                       for name, value in data.items()}

        # If output_dir is specified, write to file.
        if output_dir is not None:
            if prefix is None:
                prefix = ''
            else:
                prefix += '_'
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            for sensor_name, df in output_data.items():
                output_file = os.path.join(output_dir,
                                           prefix + sensor_name + '.csv')
                df.to_csv(output_file, na_rep=None, index=False)

        return output_data
