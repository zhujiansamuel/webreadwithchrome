from django.urls import path
from . import views
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path('post-user-text', views.post_text_function, name='PostText'),
    path('save-user-text', views.save_text_function, name="save_text_function"),
    path('login-from-chrome', views.loginfromchrome, name='login-from-chrome'),
    path('login-from-chrome/sucessful', views.loginfromchromevalidation, name='loginfromchromevalidation'),
    path('showonlinetxt', views.showonlinetext, name="showonlinetext"),
    path('showonlinetxtonhome', views.showonlinetextonhome, name="showonlinetextonhome"),
    path('testsetup', views.testsetup, name="testsetup"),
    path('quiz-generate', views.quizpage, name="quiz-page"),
    path('quiz-generate/postquiz', views.testquizgenerator, name="quiz"),
    path('quiz-generate/test', views.displayquiz, name="displayquiz"),
    path('text/<str:slug>', views.onlinetextpost, name="onlinetextpost"),
    path('onlinetextcomment', views.onlinetextcomment, name="onlinetextcomment"),
    path('testgenerate', views.testgenerate, name="testgenerate"),
    path('answercheck', views.answercheck, name="answercheck"),
    path('delonlinetext', views.del_onlinetext, name="delonlinetext"),

]
