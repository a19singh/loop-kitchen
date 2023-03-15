import asyncio
import logging
from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response

from .models import Report
from .serializers import ReportSerializer


logger = logging.getLogger(__name__)


class ReportView(viewsets.ModelViewSet):
    """
    Model View to Generate and fetch report
    """

    queryset = Report.objects.all()
    serializer_class = ReportSerializer

    def create(self, request, *args, **kwargs):
        """
        Overwritten create method
        """
        try:
            report_obj = Report.objects.create()
            work_queue = asyncio.Queue()
            await work_queue.put(report_obj)
            await asyncio.gather(self.generate_report(
                report_obj.report_id,
                work_queue
            ))
            # async call to generate report and update status
            serialized_data = ReportSerializer(report_obj)
            return Response(serialized_data.data, status.HTTP_201_CREATED)

        except Exception as e:
            data = {}
            logger.error(f"Report Generation failed: {e}")
            return Response(data, status.HTTP_400_BAD_REQUEST)

    async def generate_report(self, report_id, work_queue):
        """
        Async method to handle report generation
        """

