"""
Helios Alerts API.

Methods are meant to represent the core functionality in the developer
documentation.  Some may have additional functionality for convenience.

"""
import logging

from helios.core.mixins import SDKCore, IndexMixin, ShowMixin

logger = logging.getLogger(__name__)


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

    def __init__(self, session):
        """
        Initialize Alerts instance.

        Args:
            session (helios.HeliosSession): A HeliosSession instance.

        """
        super().__init__(session)

    def index(self, **kwargs):
        """
        Get alerts matching the provided spatial, text, or
        metadata filters.

        The maximum skip value is 4000. If this is reached, truncated results
        will be returned. You will need to refine your query to avoid this.

        .. _alerts_index_documentation: https://helios.earth/developers/api/alerts/#index

        Args:
            **kwargs: Any keyword arguments found in the alerts_index_documentation_.

        Returns:
            tuple: A tuple containing:
                feature_collection (:class:`AlertsFeatureCollection <helios.alerts_api.AlertsFeatureCollection>`):
                    Alerts feature collection.
                failed (list of :class:`Record <helios.core.structure.Record>`):
                    Failed API call records.

        """

        succeeded, failed = super().index(**kwargs)

        content = []
        for record in succeeded:
            for features in record.content['features']:
                content.append(AlertsFeature(features))

        return AlertsFeatureCollection(content), failed

    def show(self, alert_ids):
        """
        Get attributes for alerts.

        Args:
            alert_ids (str or list of strs): Helios alert ID(s).

        Returns:
            tuple: A tuple containing:
                feature_collection (:class:`AlertsFeatureCollection <helios.alerts_api.AlertsFeatureCollection>`):
                    Alerts feature collection.
                failed (list of :class:`Record <helios.core.structure.Record>`):
                    Failed API call records.

        """

        succeeded, failed = super().show(alert_ids)

        content = []
        for record in succeeded:
            content.append(AlertsFeature(record.content))

        return AlertsFeatureCollection(content), failed


class AlertsFeature:
    """
    Individual Alert GeoJSON feature.

    Attributes:
        area_description (str): 'areaDesc' value for the feature.
        bbox (list of floats): 'bbox' value for the feature.
        category (str): 'category' value for the feature.
        certainty (str): 'certainty' value for the feature.
        country (str): 'country' value for the feature.
        description (str): 'description' value for the feature.
        effective (str): 'effective' value for the feature.
        event (str): 'event' value for the feature.
        expires (str): 'expires' value for the feature.
        headline (str): 'headline' value for the feature.
        id (str): 'id' value for the feature.
        json (dict): Raw 'json' for the feature.
        origin (str): 'origin' value for the feature.
        severity (str): 'severity' value for the feature.
        states (list of strs): 'states' value for the feature.
        status (str): 'status' value for the feature.
        urgency (str): 'urgency' value for the feature.

    """

    def __init__(self, feature):
        self.json = feature

    @property
    def area_description(self):
        return self.json['properties'].get('areaDesc')

    @property
    def bbox(self):
        return self.json.get('bbox')

    @property
    def category(self):
        return self.json['properties'].get('category')

    @property
    def certainty(self):
        return self.json['properties'].get('certainty')

    @property
    def country(self):
        return self.json['properties'].get('country')

    @property
    def description(self):
        return self.json['properties'].get('description')

    @property
    def effective(self):
        return self.json['properties'].get('effective')

    @property
    def event(self):
        return self.json['properties'].get('event')

    @property
    def expires(self):
        return self.json['properties'].get('expires')

    @property
    def headline(self):
        return self.json['properties'].get('headline')

    @property
    def id(self):
        return self.json.get('id')

    @property
    def origin(self):
        return self.json['properties'].get('origin')

    @property
    def severity(self):
        return self.json['properties'].get('severity')

    @property
    def states(self):
        return self.json['properties'].get('states')

    @property
    def status(self):
        return self.json['properties'].get('status')

    @property
    def urgency(self):
        return self.json['properties'].get('urgency')


class AlertsFeatureCollection:
    """
    Collection of GeoJSON features obtained via the Alerts API.

    Convenience properties are available to extract values from every feature.

    Attributes:
        features (list of :class:`AlertsFeature <helios.alerts_api.AlertsFeature>`):
            All features returned from a query.

    """

    def __init__(self, features):
        self.features = features

    @property
    def area_description(self):
        """'areaDesc' values for every feature."""
        return [x.area_description for x in self.features]

    @property
    def bbox(self):
        """'bbox' values for every feature."""
        return [x.bbox for x in self.features]

    @property
    def category(self):
        """'category' values for every feature."""
        return [x.category for x in self.features]

    @property
    def certainty(self):
        """'certainty' values for every feature."""
        return [x.certainty for x in self.features]

    @property
    def country(self):
        """'country' values for every feature."""
        return [x.country for x in self.features]

    @property
    def description(self):
        """'description' values for every feature."""
        return [x.description for x in self.features]

    @property
    def effective(self):
        """'effective' values for every feature."""
        return [x.effective for x in self.features]

    @property
    def event(self):
        """'event' values for every feature."""
        return [x.event for x in self.features]

    @property
    def expires(self):
        """'expires' values for every feature."""
        return [x.expires for x in self.features]

    @property
    def headline(self):
        """'headline' values for every feature."""
        return [x.headline for x in self.features]

    @property
    def id(self):
        """'id' values for every feature."""
        return [x.id for x in self.features]

    @property
    def json(self):
        """Raw 'json' for every feature."""
        return [x.json for x in self.features]

    @property
    def origin(self):
        """'origin' values for every feature."""
        return [x.origin for x in self.features]

    @property
    def severity(self):
        """'severity' values for every feature."""
        return [x.severity for x in self.features]

    @property
    def states(self):
        """'states' values for every feature."""
        return [x.states for x in self.features]

    @property
    def status(self):
        """'status' values for every feature."""
        return [x.status for x in self.features]

    @property
    def urgency(self):
        """'urgency' values for every feature."""
        return [x.urgency for x in self.features]
