from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Post, Comment, PostView
from .serializers import PostSerializer, CommentSerializer
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated


class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user
    
    
class PostListCreateView(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return Post.objects.all().order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class PostRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthorOrReadOnly]
    queryset = Post.objects.all()
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if request.user.is_authenticated or request.user != instance.author:
            instance.views_count += 1
            instance.save(update_fields=['views_count'])
        
        return super().retrieve(request, *args, **kwargs)

class LikePostView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, post_id):
        post = Post.objects.get(id=post_id)
        post.likes.add(request.user)
        return Response({'message': 'Post liked'})

class UnlikePostView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, post_id):
        post = Post.objects.get(id=post_id)
        post.likes.remove(request.user)
        return Response({'message': 'Post unliked'})

class CommentCreateView(generics.CreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        post_id = self.kwargs.get('post_id')
        post = Post.objects.get(id=post_id)
        serializer.save(author=self.request.user, post=post)

class CommentUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Comment.objects.all()

    def get_queryset(self):
        return Comment.objects.filter(author=self.request.user)


class ExplorePostsView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # ✅ show ALL posts (including own posts)
        return Post.objects.all().order_by("-created_at")



class PostAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, post_id):
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({'error': 'Post not found.'}, status=404)

        data = {
            'post_id': post.id,
            'title': post.title,
            'likes_count': post.likes.count(),
            'comments_count': post.comments.count(),
            'views_count': post.views_count,
            'created_at': post.created_at,
        }
        return Response(data)

class PostViewMarkView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({"error": "Post not found"}, status=404)

        obj, created = PostView.objects.get_or_create(post=post, user=request.user)
        if created:
            post.views_count += 1
            post.save(update_fields=["views_count"])

        return Response({"views_count": post.views_count})
    
class FollowingPostsView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        following_users = self.request.user.following.all()
        return Post.objects.filter(author__in=following_users).order_by("-created_at")


