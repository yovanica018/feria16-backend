from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models import AREA


class AreaGeoSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = AREA
        geo_field = "geometria"
        fields = (
            "id_area",
            "tipo_area",
            "descripcion",
            "color",
        )