from demo.views import Index
from django.urls.conf import path

app_name = 'demo'
urlpatterns = [
    path("", Index.as_view(), name="index"),
]