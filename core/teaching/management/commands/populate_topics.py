from django.core.management.base import BaseCommand
from teaching.models import ConversationTopic

class Command(BaseCommand):
    help = 'Populate initial conversation topics'

    def handle(self, *args, **options):
        topics = [
            {
                'name': 'Independence Day holiday',
                'description': 'Discussing Independence Day celebrations, traditions, and experiences'
            },
            {
                'name': 'favorite food',
                'description': 'Talking about favorite foods, cooking, and dining experiences'
            },
            {
                'name': 'travel experiences',
                'description': 'Sharing travel stories, destinations, and cultural experiences'
            },
            {
                'name': 'hobbies and interests',
                'description': 'Discussing personal hobbies, interests, and leisure activities'
            },
            {
                'name': 'weather and seasons',
                'description': 'Conversations about weather, climate, and seasonal activities'
            },
            {
                'name': 'family and friends',
                'description': 'Talking about family relationships and friendships'
            },
            {
                'name': 'work and career',
                'description': 'Discussing jobs, careers, and professional experiences'
            },
            {
                'name': 'movies and entertainment',
                'description': 'Conversations about movies, TV shows, and entertainment'
            },
            {
                'name': 'sports and fitness',
                'description': 'Discussing sports, exercise, and healthy lifestyle'
            },
            {
                'name': 'technology and gadgets',
                'description': 'Talking about technology, smartphones, and digital life'
            },
            {
                'name': 'education and learning',
                'description': 'Conversations about school, learning, and personal development'
            },
            {
                'name': 'shopping and fashion',
                'description': 'Discussing shopping experiences, fashion, and personal style'
            }
        ]

        created_count = 0
        for topic_data in topics:
            topic, created = ConversationTopic.objects.get_or_create(
                name=topic_data['name'],
                defaults={'description': topic_data['description']}
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created topic: {topic.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Topic already exists: {topic.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} new topics')
        ) 