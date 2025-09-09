from django.urls import path
from .views import (
    FollowingPostsView, PostListCreateView, PostRetrieveUpdateDeleteView, 
    LikePostView, PostViewMarkView, UnlikePostView, 
    CommentCreateView, CommentUpdateDeleteView, ExplorePostsView, PostAnalyticsView
)

urlpatterns = [
    path('', PostListCreateView.as_view()),
    path('<int:pk>/', PostRetrieveUpdateDeleteView.as_view()),
    path('<int:post_id>/like/', LikePostView.as_view()),
    path('<int:post_id>/unlike/', UnlikePostView.as_view()),
    path('<int:post_id>/comment/', CommentCreateView.as_view()),
    path('comment/<int:pk>/', CommentUpdateDeleteView.as_view()),
    path('explore/', ExplorePostsView.as_view(), name='explore-posts'),
    path('following/', FollowingPostsView.as_view(), name='following-posts'),
    path('<int:post_id>/analytics/', PostAnalyticsView.as_view(), name='post-analytics'),
    path("<int:post_id>/view/", PostViewMarkView.as_view(), name="post-view"),
    
]
