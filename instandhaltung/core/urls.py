from django.urls import path
from . import views

urlpatterns = [
    path('', views.machine_list, name='machine_list'),
    path('order/create/<int:machine_id>/', views.order_create, name='order_create'),
    path('machine/<int:machine_id>/', views.machine_detail, name='machine_detail'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('machine/<int:machine_id>/log/<int:log_id>/update/', views.log_update, name='log_update'),
    path('orders/', views.order_list, name='order_list'),
]