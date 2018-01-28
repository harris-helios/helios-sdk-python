"""
SDK for the Helios Observations API.

Methods are meant to represent the core functionality in the developer
documentation.  Some may have additional functionality for convenience.

"""
import logging
from contextlib import closing
from itertools import repeat
from multiprocessing.pool import ThreadPool

from helios.core import SDKCore, IndexMixin, ShowMixin, \
    DownloadImagesMixin, RequestManager
from helios.utilities import logging_utils


class Observations(DownloadImagesMixin, ShowMixin, IndexMixin, SDKCore):
    """
    The Observations API provides ground-truth data generated by the Helios
    analytics.

    """

    core_api = 'observations'

    def __init__(self, session=None):
        super(Observations, self).__init__(session=session)
        self.logger = logging.getLogger(__name__)

    def index(self, **kwargs):
        """
        Return a list of observations matching the provided spatial, text, or
        metadata filters.

        The maximum skip value is 4000. If this is reached, truncated results
        will be returned. You will need to refine your query to avoid this.

        Args:
            **kwargs: Any keyword arguments found in the documentation.

        Returns:
             list: GeoJSON feature collections.

        """
        return super(Observations, self).index(**kwargs)

    def show(self, observation_id):
        """
        Return the attributes for a single observation.

        Args:
            observation_id (str): Observation ID.

        Returns:
            dict: GeoJSON feature.

        """
        return super(Observations, self).show(observation_id)

    @logging_utils.log_entrance_exit
    def preview(self, observation_ids, check_for_duds=True):
        """
        Return a preview image for an observation.

        This API call will attempt to filter out unusable images
        (e.g. full image text/logos, etc.) and will return the most recent
        image for the observation time period.

        Args:
            observation_ids (str or sequence of strs): list of observation IDs.
            check_for_duds (bool, optional): Flag to remove dud images from
                results. Defaults to True.

        Returns:
            sequence of strs: Image URLs.

        """
        # Force iterable
        if not isinstance(observation_ids, (list, tuple)):
            observation_ids = [observation_ids]
        n_obs = len(observation_ids)

        # Log entrance
        self.logger.info('Entering preview(%s observation_ids)', n_obs)

        # Get number of threads
        num_threads = min(self.max_threads, n_obs)

        # Process ids.
        if num_threads > 1:
            with closing(ThreadPool(num_threads)) as thread_pool:
                results = thread_pool.map(self.__preview_worker,
                                          zip(observation_ids, repeat(check_for_duds)))
        else:
            results = [self.__preview_worker((observation_ids[0], check_for_duds))]

        # Remove errors, if they exist
        results = [x for x in results if x != -1]

        # Check results
        n_successful = len(results)
        message = 'Leaving preview({} out of {} successful)'.format(n_successful, n_obs)

        if n_successful == 0:
            self.logger.error(message)
            return -1
        elif n_successful < n_obs:
            self.logger.warning(message)
        else:
            self.logger.info(message)

        return results

    def __preview_worker(self, args):
        observation_id, check_for_duds = args

        query_str = '{}/{}/{}/preview'.format(self.base_api_url,
                                              self.core_api,
                                              observation_id)

        try:
            resp = self.request_manager.get(query_str)
            redirect_url = resp.url[0:resp.url.index('?')]
        except Exception:
            return -1

        # Check header for dud statuses.
        if check_for_duds:
            try:
                # Redirect URLs do not use api credentials
                resp2 = self.request_manager.head(redirect_url,
                                                  use_api_cred=False)
            except Exception:
                return -1

            if self.check_headers_for_dud(resp2.headers):
                self.logger.info('preview query returned dud image: %s',
                                 query_str)
                return None

        return redirect_url
