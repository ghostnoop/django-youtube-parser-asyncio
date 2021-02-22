from django.urls import path

from parsing import views

app_name = "parsing"
urlpatterns = [
    path(r'hours/<int:hour>', views.RouteStatisticPerHour.as_view(), name="rout_stat_hour"),
    path(r'history', views.HistoryView.as_view(), name="history"),
    path(r'detail/<int:pk>', views.DetailView.as_view(), name='detail'),
    path(r'keys/<int:hours>', views.KeysView.as_view(), name="keys"),
    path(r'', views.RouteStatisticAsync.as_view(), name="rout_stat"),
    # path(r'ss/', views.RouteStatisticAsync.as_view(), name="rout_stats")
]
# sudo systemctl restart gunicorn
