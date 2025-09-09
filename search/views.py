from rest_framework import generics, permissions
from posts.models import Post
from accounts.models import User
from posts.serializers import PostSerializer
from accounts.serializers import UserSerializer
from rest_framework.response import Response
from rest_framework.views import APIView

class SearchAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        query = request.query_params.get('q', '')

        users = User.objects.filter(username__icontains=query)
        posts = Post.objects.filter(title__icontains=query)

        user_serializer = UserSerializer(users, many=True)
        post_serializer = PostSerializer(posts, many=True)

        return Response({
            'users': user_serializer.data,
            'posts': post_serializer.data,
        })
