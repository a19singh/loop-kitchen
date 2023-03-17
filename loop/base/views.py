import logging
from rest_framework import viewsets, status
from rest_framework.response import Response
from multiprocessing import Process
import threading
from asgiref.sync import sync_to_async

from .models import Report
from .serializers import ReportSerializer
from .report_generator import ReportGenerator


logger = logging.getLogger(__name__)


class ReportView(viewsets.ModelViewSet):
    """
    Model View to Generate and fetch report
    """

    queryset = Report.objects.all()
    serializer_class = ReportSerializer

    def create(self, request, *args, **kwargs):
        """
        Overwritten create method to create a report instance
        and make a threaded call for report generation

        Returns:
        --------
            HttpResponse(data, status_code)
        """
        try:
            report_obj = Report.objects.create()
            generator_obj = ReportGenerator()
            # threaded call to generate report and update status
            p = threading.Thread(
                target=generator_obj.generate_report,
                args=(report_obj,)
            )
            p.start()
            serialized_data = ReportSerializer(report_obj)
            return Response(serialized_data.data, status.HTTP_201_CREATED)

        except Exception as e:
            data = {}
            logger.error(f"Report Generation failed: {e}")
            return Response(data, status.HTTP_400_BAD_REQUEST)

