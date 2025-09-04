from django.urls import path
from .views import SuggestView, SearchView, TrendingView, RecommendationView, SearchHistoryView, SearchAnalyticsView, SearchFeedbackView

urlpatterns = [
    path('suggest/', SuggestView.as_view(), name='suggest'),
    path('trending/', TrendingView.as_view(), name='trending'),
    path('recommendations/me/', RecommendationView.as_view(), name='recommendations-me'),
    path('history/', SearchHistoryView.as_view(), name='search-history'),
    path('analytics/', SearchAnalyticsView.as_view(), name='search-analytics'),
    path('feedback/', SearchFeedbackView.as_view(), name='search-feedback'),
    path('', SearchView.as_view(), name='search'),
]
