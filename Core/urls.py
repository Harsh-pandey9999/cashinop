from django.urls import path
from . import views
from uuid import UUID  # optional for clarity

# User URLs
user_urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('logout/', views.logout, name='logout'),
    path('locked/', views.account_locked, name='account_locked'),
    path('user/dashboard/', views.user_dashboard, name='user_dashboard'),
    path('user/profile/', views.user_profile, name='user_profile'),
    path('user/clicks/', views.user_clicks, name='user_clicks'),
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),
]

# Admin URLs (using namespace to prevent conflicts)
admin_urlpatterns = [
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/old/', views.admin_dashboard, name='admin_dashboard_old'),
    path('approve-users/', views.approve_users, name='approve_users'),
    path('approve/<str:username>/', views.approve_user, name='approve_user'),
    path('posts/', views.posts, name='posts'),
    path('toggle-post/<str:post_id>', views.toggle_post_visibility, name='toggle_post'),
    path('add-post/', views.add_post, name='add_post'),
    path('user_detail/<str:username>/', views.user_info, name='user_details'),
    path('post/<str:pk>/delete/', views.delete_post, name='delete_post'),
    path('post/<str:pk>/edit/', views.edit_post, name='edit_post'),
    path('logout/', views.admin_logout, name='admin_logout'),
    path('contact/', views.contact_update, name='contact_update'),
    path('site-settings/', views.site_settings_update, name='site_settings_update'),
    path('manage-users/', views.manage_users, name='manage_users'),
    path('manage-users/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('manage-users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('about/', views.about, name='about'),
    path('add-about/', views.add_about, name='add_about'),
    path('about/<str:pk>/delete/', views.delete_about, name='delete_about'),
    path('about/<str:pk>/edit/', views.edit_about, name='edit_about'),
]

# Public URLs
public_urlpatterns = [
    path('about/', views.about_page, name='about_page'),
    path('contact/', views.contact_page, name='contact_page'),
    path('terms/', views.terms_page, name='terms'),
    path('privacy/', views.privacy_page, name='privacy'),
    path('card/<uuid:card_id>/', views.redirect_to_card_link, name='redirect_to_card_link'),
]

# Combine all URL patterns
urlpatterns = user_urlpatterns + admin_urlpatterns + public_urlpatterns

# Combine all URLs
urlpatterns = user_urlpatterns + admin_urlpatterns + public_urlpatterns