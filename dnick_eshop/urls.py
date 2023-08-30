"""
URL configuration for dnick_eshop project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('products/', views.products, name='products'),
    path('products/<slug:slug>', views.product_detail, name='product_detail'),
    path('categories/', views.categories, name='categories'),
    path('categories/<slug:slug>', views.category_list, name='category_list'),
    path('seller/<str:seller_username>', views.seller_profile, name='seller_profile'),
    path('reviews/<slug:slug>', views.reviews, name='reviews'),
    path('cart/', views.cart, name='cart'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('orders/', views.orders, name='orders'),
    path('add_product/', views.add_product_to_shop, name='add_product_to_shop'),
    path('checkout/', views.checkout, name='checkout'),
    path('add_to_cart', views.add_to_cart, name='add_to_cart'),
    path('add_review_to_product', views.add_review_to_product, name='add_review_to_product'),
    path('save_review', views.save_review, name='save_review'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
