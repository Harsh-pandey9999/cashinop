from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from Core.models import BlogPost

User = get_user_model()

class Command(BaseCommand):
    help = 'Adds sample blog posts to the database'

    def handle(self, *args, **options):
        author = User.objects.filter(username='admin').first()
        if not author:
            self.stdout.write(self.style.ERROR('No admin user found!'))
            return

        posts = [
            {
                'title': 'The Psychology of Winning: How Casino Players Think',
                'slug': 'psychology-of-winning',
                'content': '''
                    <h2>Unlocking the Mind of a Winner</h2>
                    <p>Ever wondered what separates the casual player from the consistent winner? It's not just luck—it's mindset. In this post, we dive deep into the psychology of casino winners, exploring risk-taking, discipline, and the thrill of the game.</p>
                    <ul>
                        <li><b>Risk vs. Reward:</b> Winners know when to take calculated risks and when to walk away.</li>
                        <li><b>Emotional Control:</b> Staying cool under pressure is key to long-term success.</li>
                        <li><b>Learning from Losses:</b> Every loss is a lesson, not a defeat.</li>
                    </ul>
                    <img src="https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=800&q=80" alt="Winning Mindset" style="width:100%;border-radius:12px;margin:24px 0;">
                    <p>Master your mind, and you'll master the game.</p>
                ''',
                'meta_description': 'Explore the psychology behind casino winners and learn how to develop a winning mindset.',
                'meta_keywords': 'casino, psychology, winning, mindset, risk, reward',
                'published': True,
                'published_at': timezone.now(),
                'is_featured': True
            },
            {
                'title': "2024's Hottest Casino Games You Can't Miss",
                'slug': 'hottest-casino-games-2024',
                'content': '''
                    <h2>Top Games Taking the Casino World by Storm</h2>
                    <p>This year, innovation meets excitement! Here are the must-try games of 2024:</p>
                    <ol>
                        <li><b>Neon Nights Slots:</b> Dazzling visuals and huge jackpots.</li>
                        <li><b>Quantum Blackjack:</b> A futuristic twist on a classic favorite.</li>
                        <li><b>Lightning Roulette:</b> Electrifying multipliers and fast-paced action.</li>
                        <li><b>Speed Baccarat:</b> For those who crave quick thrills.</li>
                        <li><b>Virtual Poker Tournaments:</b> Compete globally from your living room.</li>
                    </ol>
                    <img src="https://images.unsplash.com/photo-1511512578047-dfb367046420?auto=format&fit=crop&w=800&q=80" alt="Casino Games 2024" style="width:100%;border-radius:12px;margin:24px 0;">
                    <p>Which game will you try first?</p>
                ''',
                'meta_description': 'Discover the most exciting and innovative casino games of 2024.',
                'meta_keywords': 'casino, games, 2024, slots, blackjack, roulette, baccarat, poker',
                'published': True,
                'published_at': timezone.now(),
                'is_featured': True
            },
            {
                'title': 'Affiliate Success: How to Maximize Your Casino Partner Earnings',
                'slug': 'affiliate-success-casino-partner',
                'content': '''
                    <h2>Boost Your Earnings with Proven Strategies</h2>
                    <p>Ready to become a top casino affiliate? Here's how:</p>
                    <ul>
                        <li><b>Know Your Audience:</b> Use analytics to tailor your content and offers.</li>
                        <li><b>SEO Mastery:</b> Optimize your site for high-value keywords and evergreen content.</li>
                        <li><b>Trust & Transparency:</b> Build loyalty with honest reviews and clear disclosures.</li>
                        <li><b>Test & Tweak:</b> A/B test your banners and calls-to-action for better results.</li>
                    </ul>
                    <img src="https://images.unsplash.com/photo-1464983953574-0892a716854b?auto=format&fit=crop&w=800&q=80" alt="Affiliate Success" style="width:100%;border-radius:12px;margin:24px 0;">
                    <p>Consistency and creativity are your keys to affiliate success!</p>
                ''',
                'meta_description': 'Learn actionable strategies to increase your casino affiliate earnings.',
                'meta_keywords': 'casino, affiliate, earnings, partner, strategy, SEO',
                'published': True,
                'published_at': timezone.now(),
                'is_featured': True
            }
        ]

        for post_data in posts:
            try:
                post = BlogPost.objects.create(author=author, **post_data)
                self.stdout.write(self.style.SUCCESS(f'Created blog post: {post.title}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating post {post_data["title"]}: {str(e)}'))

        self.stdout.write(self.style.SUCCESS('Finished creating blog posts!')) 