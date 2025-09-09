# 📚 SkillSync Backend API Documentation

## ✅ Project Overview
SkillSync is a collaborative platform to:
- Share, explore, and engage with learning resources.
- Follow/unfollow users.
- Comment, like, and explore posts.
- Search users and posts.
- Analytics for user engagement.
- JWT Authentication with cookie storage.
- Password reset with OTP via email.

---

## ✅ API Endpoints Summary

| Endpoint                                   | Method | Description                       | Auth |
| ------------------------------------------ | ------ | --------------------------------- | ---- |
| `/api/accounts/register/`                  | POST   | Register new user                 | ❌   |
| `/api/accounts/login/`                     | POST   | Login and get JWT tokens          | ❌   |
| `/api/accounts/logout/`                    | POST   | Logout user                       | ✅   |
| `/api/accounts/profile/`                   | GET    | Get logged-in user's profile      | ✅   |
| `/api/accounts/profile/`                   | PATCH  | Update profile                    | ✅   |
| `/api/accounts/follow/<user_id>/`          | POST   | Follow user                       | ✅   |
| `/api/accounts/unfollow/<user_id>/`        | POST   | Unfollow user                     | ✅   |
| `/api/accounts/users/`                     | GET    | List all users                    | ❌   |
| `/api/accounts/users/<id>/`                | GET    | User detail                       | ❌   |
| `/api/accounts/users/<user_id>/posts/`     | GET    | List posts by a specific user     | ❌   |
| `/api/accounts/liked-posts/`               | GET    | List logged-in user's liked posts | ✅   |
| `/api/accounts/forgot-password/`           | POST   | Send OTP to reset password        | ❌   |
| `/api/accounts/verify-otp/`                | POST   | Verify OTP                        | ❌   |
| `/api/accounts/reset-password/`            | POST   | Reset password                    | ❌   |
| `/api/posts/`                              | GET    | List all posts                    | ❌   |
| `/api/posts/`                              | POST   | Create a post                     | ✅   |
| `/api/posts/<post_id>/`                    | PATCH  | Update a post                     | ✅   |
| `/api/posts/<post_id>/`                    | DELETE | Delete a post                     | ✅   |
| `/api/posts/<post_id>/like/`               | POST   | Like a post                       | ✅   |
| `/api/posts/<post_id>/unlike/`             | POST   | Unlike a post                     | ✅   |
| `/api/posts/<post_id>/comment/`            | POST   | Add a comment                     | ✅   |
| `/api/posts/comment/<comment_id>/`         | PATCH  | Update a comment                  | ✅   |
| `/api/posts/comment/<comment_id>/`         | DELETE | Delete a comment                  | ✅   |
| `/api/posts/explore/`                      | GET    | Posts from followed users         | ✅   |
| `/api/posts/<post_id>/analytics/`          | GET    | Get likes, comments, views count  | ✅   |
| `/api/analytics/my-analytics/`             | GET    | My profile analytics              | ✅   |
| `/api/search/`                             | GET    | Search users and posts            | ❌   |

---

# 📝 Example API Requests & Responses

---

## Register

**POST** `/api/accounts/register/`

**Request**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "securepassword"
}
```

**Response**
```json
{
  "message": "User registered successfully"
}
```

---

## Login

**POST** `/api/accounts/login/`

**Request**
```json
{
  "username": "john_doe",
  "password": "securepassword"
}
```

**Response**
```json
{
  "message": "Login successful",
  "access": "<token>",
  "refresh": "<refresh_token>"
}
```

---

## Forgot Password

**POST** `/api/accounts/forgot-password/`

**Request**
```json
{
  "email": "john@example.com"
}
```

**Response**
```json
{
  "message": "OTP sent to your email"
}
```

---

## Verify OTP

**POST** `/api/accounts/verify-otp/`

**Request**
```json
{
  "email": "john@example.com",
  "otp": "123456"
}
```

**Response**
```json
{
  "message": "OTP verified successfully"
}
```

---

## Reset Password

**POST** `/api/accounts/reset-password/`

**Request**
```json
{
  "email": "john@example.com",
  "new_password": "newSecurePass123"
}
```

**Response**
```json
{
  "message": "Password reset successful"
}
```

---

## Create Post

**POST** `/api/posts/`

**Request**
```json
{
  "title": "Learn Django REST Framework",
  "description": "Great tutorial to build APIs",
  "external_link": "https://example.com",
  "image_url": "https://example.com/image.jpg",
  "category": "Backend"
}
```

**Response**
```json
{
  "id": 1,
  "title": "Learn Django REST Framework",
  "description": "Great tutorial to build APIs",
  "external_link": "https://example.com",
  "image_url": "https://example.com/image.jpg",
  "category": "Backend",
  "author": "john_doe",
  "created_at": "2025-07-20T10:10:00Z"
}
```

---

## Like a Post

**POST** `/api/posts/<post_id>/like/`

**Response**
```json
{
  "message": "Post liked"
}
```

---

## Explore Posts

**GET** `/api/posts/explore/`

**Response**
```json
[
  {
    "id": 2,
    "title": "React Hooks Guide",
    "author": "jane_smith",
    "category": "Frontend",
    "created_at": "2025-07-17T12:00:00Z"
  },
  {
    "id": 1,
    "title": "Learn Django REST Framework",
    "author": "john_doe",
    "category": "Backend",
    "created_at": "2025-07-15T13:30:00Z"
  }
]
```

---

## Analytics for My Profile

**GET** `/api/analytics/my-analytics/`

**Response**
```json
{
  "total_posts": 5,
  "total_followers": 10,
  "total_following": 3
}
```

---

## Search

**GET** `/api/search/?q=django`

**Response**
```json
{
  "users": [
    { "id": 1, "username": "django_dev" }
  ],
  "posts": [
    { "id": 5, "title": "Django REST Framework Tutorial" }
  ]
}
```

---

## Password Reset Flow

1. **Request OTP →** `/api/accounts/forgot-password/`  
   **Response:**
   ```json
   {
     "message": "OTP sent to your email"
   }
   ```
2. **Verify OTP →** `/api/accounts/verify-otp/`  
   **Response:**
   ```json
   {
     "message": "OTP verified successfully"
   }
   ```
3. **Reset Password →** `/api/accounts/reset-password/`  
   **Response:**
   ```json
   {
     "message": "Password reset successful"
   }
   ```

---

## Pagination

For any paginated list:  
`/api/posts/?limit=10&offset=0`

**Pagination Response Example**
```json
{
  "count": 100,
  "next": "/api/posts/?limit=10&offset=10",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Learn Django REST Framework"
    }
    // ...
  ]
}
```

---

## Notes

- Protected routes require JWT `access_token` via cookies.
- For image uploads, use [ImageKit.io](https://imagekit.io/) (**frontend handles it**).
- Analytics are computed on-demand per user/post.

---

## Next

- Frontend Implementation (React + Tailwind + Framer Motion)
- Admin email config for SMTP setup for OTPs
- Deployment to Render/Heroku.

---

## Technologies Used

- Django Rest Framework
- SimpleJWT for Authentication
- PostgreSQL / SQLite
- SMTP for Emails
- ImageKit for images

---

© 2025 SkillSync.