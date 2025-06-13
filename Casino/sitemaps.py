from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from Core.models import GameCards, About


class StaticSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return ['index', 'contact_page', 'about_page', 'terms_page', 'privacy_page', 'signin', 'signup']

    def location(self, item):
        return reverse(item)


class GameCardsSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        return GameCards.objects.filter(active=True)

    def lastmod(self, obj):
        return obj.created_at

    def location(self, obj):
        return f'/card/{obj.id}/'


class AboutSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return About.objects.all()

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return '/about-us/'
