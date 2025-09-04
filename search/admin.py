from django.contrib import admin
from .models import SearchHistory, SearchAnalytics, Recommendation, TrendingContent

@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ('query', 'user', 'results_count', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('query', 'user__email')

@admin.register(SearchAnalytics)
class SearchAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('query', 'count', 'avg_click_rate', 'last_seen_at')
    search_fields = ('query',)

@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('user', 'item_type', 'item_id', 'score', 'model_version', 'created_at')
    list_filter = ('item_type', 'model_version', 'created_at')
    search_fields = ('user__email', 'item_id')

@admin.register(TrendingContent)
class TrendingContentAdmin(admin.ModelAdmin):
    list_display = ('content_type', 'content_id', 'score', 'computed_at')
    list_filter = ('content_type', 'computed_at')
    search_fields = ('content_id',)
