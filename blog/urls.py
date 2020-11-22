from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('postcomment', views.Postcomment, name='Postcomment'),
    path('', views.bloghome, name='bloghome'),

    #下面的这个实际上就是向views.blogpost函数传递参数
    #def blogpost(request, slug):
    #slug相当于关键字参数的关键字
    path('<str:slug>', views.blogpost, name='blogpost'),
]