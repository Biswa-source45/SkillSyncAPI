from rest_framework import serializers
from .models import Post, Comment
from accounts.serializers import ProfileSerializer

class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)
    author_profile = ProfileSerializer(source='author', read_only=True)  # ✅ NEW

    class Meta:
        model = Comment
        fields = [
            'id', 'author', 'author_name', 'author_profile',
            'content', 'created_at'
        ]
        read_only_fields = ['author', 'created_at']


class PostSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)
    author_profile = ProfileSerializer(source='author', read_only=True)  # ✅ nested
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    comments = CommentSerializer(many=True, read_only=True)
    is_liked = serializers.SerializerMethodField()  # ✅ NEW

    class Meta:
        model = Post
        fields = [
            'id', 'author', 'author_name', 'author_profile',
            'title', 'description', 'external_link', 'image_url', 'category',
            'likes_count', 'comments_count', 'views_count',
            'comments', 'created_at', 'is_liked'
        ]
        read_only_fields = ['author', 'created_at', 'views_count']
        extra_kwargs = {
            "category": {"required": False, "allow_blank": True},
        }

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_is_liked(self, obj): 
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.likes.filter(id=request.user.id).exists()
        return False
