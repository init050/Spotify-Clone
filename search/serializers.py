from rest_framework import serializers
from artists.serializers import ArtistSerializer, AlbumSerializer, TrackSerializer
from playlists.serializers import PlaylistSerializer
from .models import TrendingContent, SearchAnalytics, SearchHistory, Recommendation

class SuggestionSerializer(serializers.Serializer):
    type = serializers.CharField()
    text = serializers.CharField()
    score = serializers.FloatField()

class RecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recommendation
        fields = '__all__'

class SearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchHistory
        fields = '__all__'

class SearchAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchAnalytics
        fields = '__all__'

class SearchFeedbackSerializer(serializers.Serializer):
    query = serializers.CharField()
    clicked_item = serializers.JSONField()
    position = serializers.IntegerField()

    def create(self, validated_data):
        # This is a simplified implementation.
        # In a real application, this would likely be more complex,
        # involving updating SearchAnalytics and potentially other models.
        SearchHistory.objects.create(
            user=validated_data['user'],
            query=validated_data['query'],
            clicked_item=validated_data['clicked_item'],
            results_count=0, # This would need to be passed in a real scenario
        )
        return validated_data

class TrendingContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrendingContent
        fields = '__all__'

class SearchResultSerializer(serializers.Serializer):
    type = serializers.CharField()
    score = serializers.FloatField()
    headline = serializers.CharField()
    item = serializers.SerializerMethodField()

    def get_item(self, obj):
        item_type = obj.get('type')
        instance = obj.get('instance')
        context = self.context

        if item_type == 'artist':
            return ArtistSerializer(instance, context=context).data
        if item_type == 'album':
            return AlbumSerializer(instance, context=context).data
        if item_type == 'track':
            return TrackSerializer(instance, context=context).data
        if item_type == 'playlist':
            return PlaylistSerializer(instance, context=context).data
        return None
