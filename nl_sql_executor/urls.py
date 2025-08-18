from django.urls import path
from . import views

urlpatterns = [
    path("emissions", views.nl_sql_executor, name="nl_sql_executor"),
    path("", views.nl_sql_executor, name="nl_sql_executor"),
]