from django.urls import path
from . import views

urlpatterns = [
    path(
        'get_report',
        views.ReportView.as_view({
            'get': 'list'
        })
    ),
    path(
        'get_report/<str:pk>',
        views.ReportView.as_view({
            'get': 'retrieve',
            'delete': 'destroy'
        })
    ),
    path(
        'trigger_report',
        views.ReportView.as_view({
            'post': 'create'
        })
    )
]
