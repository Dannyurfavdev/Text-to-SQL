from django.urls import path
from .views import QueryView, FrontendView, SchemaInfoView

urlpatterns = [
    path("query/", QueryView.as_view()),
    path("", FrontendView.as_view()), 
    path("schema/", SchemaInfoView.as_view()),
]