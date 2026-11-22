from django.urls import path

from . import views

app_name = 'polls'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('<int:pk>/', views.detail, name='detail'),
    path('<int:pk>/results/', views.results, name='results'),
    path('<int:question_id>/vote/', views.vote, name='vote'),
    path('signup/', views.signup, name='signup'),
    path('create/', views.create, name='create'),
    path('<int:question_id>/delete/', views.delete, name='delete'),
    path('mine/', views.my_polls, name='my_polls'),
    path('search/', views.search, name='search'),
]
