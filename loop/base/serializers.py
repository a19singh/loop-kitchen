from .models import Report
from rest_framework import serializers


class ReportSerializer(serializers.ModelSerializer):
    """
    Serializer to handle CRUD operations for Report Model
    """

    class Meta:
        model = Report
        fields = '__all__'
        read_only_fields = ('cdate', )
