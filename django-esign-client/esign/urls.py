"""
esign/urls.py
-------------
Include in your project's urls.py::

    from django.urls import path, include

    urlpatterns = [
        path('esign/', include('esign.urls')),
        ...
    ]

Endpoints
---------
POST  /esign/initiate/                  Start signing (Phase 1)
POST  /esign/callback/                  Gateway callback (Phase 2)
GET   /esign/status/<transaction_id>/   Transaction status
GET   /esign/download/<transaction_id>/ Download signed PDF
"""

from django.urls import path

from . import views

app_name = 'esign'

urlpatterns = [
    path('initiate/',                                views.ESignInitiateView.as_view(),  name='initiate'),
    path('callback/',                                views.ESignCallbackView.as_view(),  name='callback'),
    path('status/<str:transaction_id>/',             views.ESignStatusView.as_view(),    name='status'),
    path('download/<str:transaction_id>/',           views.ESignDownloadView.as_view(),  name='download'),
]
