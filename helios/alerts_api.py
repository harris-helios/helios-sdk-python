"""
Helios Alerts API.

Methods are meant to represent the core functionality in the developer
documentation.  Some may have additional functionality for convenience.

"""
import logging

from helios.core.mixins import SDKCore, IndexMixin, ShowMixin


class Alerts(ShowMixin, IndexMixin, SDKCore):
    """
    Helios alerts provide real-time severe weather alerts.

    **National Weather Service:**

    - Severe weather alerts for the United States are provided by the
      National Weather Service. These alerts cover events such as Flood
      Warnings, Severe Thunderstorm Warnings, and Special Weather Statements.

    **Helios:**

    - Alerts generated by Helios are based on the sensor measurements from
      the Observations API. These alerts represent regional areas with a high
      detection confidence and currently include: Road Wetness Watch, Poor
      Visibility Watch, and Heavy Precip Watch.

    """

    _core_api = 'alerts'

    def __init__(self, session=None):
        """
        Initialize Alerts instance.

        Args:
            session (helios.Session object, optional): An instance of the
                Session. Defaults to None. If unused a session will be
                created for you.

        """
        super(Alerts, self).__init__(session=session)
        self._logger = logging.getLogger(__name__)

    def index(self, **kwargs):
        """
        Get a list of alerts matching the provided spatial, text, or
        metadata filters.

        The maximum skip value is 4000. If this is reached, truncated results
        will be returned. You will need to refine your query to avoid this.

        .. _alerts_index_documentation: https://helios.earth/developers/api/alerts/#index

        Args:
            **kwargs: Any keyword arguments found in the alerts_index_documentation_.

        Returns:
             list: GeoJSON feature collections.

        """
        return super(Alerts, self).index(**kwargs)

    def show(self, alert_ids):
        """
        Get attributes for alerts.

        Args:
            alert_ids (str or sequence of strs): Helios alert ID(s).

        Returns:
            :class:`DataContainer <helios.core.records.DataContainer>`:
            Container of :class:`Record <helios.core.records.Record>`.

        """
        return super(Alerts, self).show(alert_ids)
