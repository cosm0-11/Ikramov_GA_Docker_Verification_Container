from django.conf import settings 
from django.conf.urls.static import static # импортируем функцию для обработки статических файлов
from django.contrib import admin
from django.urls import path, include # импортируем функцию для подключения URL-маршрутов приложений
from web_container import views  # импортируем представления из приложения web_container

urlpatterns = [ # определяем список URL-маршрутов для всего проекта
    path("admin/", admin.site.urls),
    path("", views.index, name="index"),
    path("create/", views.create_file_view, name="create_file"),
    path("delete/", views.delete_file_view, name="delete_file"),
    path("sign/", views.sign_view, name="sign_file"),
    path("verify/", views.verify_view, name="verify_file"),
    path("compromise/", views.compromise_view, name="compromise_file"),
    path("quarantine/", views.quarantine_view, name="quarantine"),
    path("quarantine/clear/", views.clear_quarantine_view, name="clear_quarantine"),
    path("simulation/", views.simulation_view, name="simulation"),
    path("simulation/clear/", views.clear_simulation_view, name="clear_simulation"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # добавляем маршрут для обработки медиафайлов в режиме отладки