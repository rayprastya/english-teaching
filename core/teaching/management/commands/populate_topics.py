from django.core.management.base import BaseCommand
from teaching.models import ConversationTopic

class Command(BaseCommand):
    help = 'Populate initial conversation topics with difficulty levels'

    def handle(self, *args, **options):
        topics = [
            # Easy topics - first 5 conversations
            {
                'name': 'favorite food',
                'description': 'Talking about favorite foods, cooking, and dining experiences',
                'difficulty_level': 'easy'
            },
            {
                'name': 'weather and seasons',
                'description': 'Conversations about weather, climate, and seasonal activities',
                'difficulty_level': 'easy'
            },
            {
                'name': 'hobbies and interests',
                'description': 'Discussing personal hobbies, interests, and leisure activities',
                'difficulty_level': 'easy'
            },
            {
                'name': 'family and friends',
                'description': 'Talking about family relationships and friendships',
                'difficulty_level': 'easy'
            },
            {
                'name': 'daily routine',
                'description': 'Discussing daily activities, schedules, and routines',
                'difficulty_level': 'easy'
            },
            
            # Medium topics - next 5 conversations
            {
                'name': 'travel experiences',
                'description': 'Sharing travel stories, destinations, and cultural experiences',
                'difficulty_level': 'medium'
            },
            {
                'name': 'work and career',
                'description': 'Discussing jobs, careers, and professional experiences',
                'difficulty_level': 'medium'
            },
            {
                'name': 'movies and entertainment',
                'description': 'Conversations about movies, TV shows, and entertainment',
                'difficulty_level': 'medium'
            },
            {
                'name': 'technology and gadgets',
                'description': 'Talking about technology, smartphones, and digital life',
                'difficulty_level': 'medium'
            },
            {
                'name': 'shopping and fashion',
                'description': 'Discussing shopping experiences, fashion, and personal style',
                'difficulty_level': 'medium'
            },
            
            # Hard topics - last 5 conversations
            {
                'name': 'Independence Day holiday',
                'description': 'Discussing Independence Day celebrations, traditions, and experiences',
                'difficulty_level': 'hard'
            },
            {
                'name': 'education and learning',
                'description': 'Conversations about school, learning, and personal development',
                'difficulty_level': 'hard'
            },
            {
                'name': 'sports and fitness',
                'description': 'Discussing sports, exercise, and healthy lifestyle',
                'difficulty_level': 'hard'
            },
            {
                'name': 'environment and nature',
                'description': 'Talking about environmental issues, nature, and sustainability',
                'difficulty_level': 'hard'
            },
            {
                'name': 'business and economics',
                'description': 'Discussing business concepts, economics, and market trends',
                'difficulty_level': 'hard'
            }
        ]

        created_count = 0
        updated_count = 0
        
        for topic_data in topics:
            topic, created = ConversationTopic.objects.get_or_create(
                name=topic_data['name'],
                defaults={
                    'description': topic_data['description'],
                    'difficulty_level': topic_data['difficulty_level']
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created topic: {topic.name} ({topic.get_difficulty_level_display()})')
                )
            else:
                # Update existing topic if difficulty level is different
                if topic.difficulty_level != topic_data['difficulty_level']:
                    topic.difficulty_level = topic_data['difficulty_level']
                    topic.description = topic_data['description']
                    topic.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Updated topic: {topic.name} to {topic.get_difficulty_level_display()}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Topic already exists: {topic.name} ({topic.get_difficulty_level_display()})')
                    )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} new topics and updated {updated_count} existing topics')
        ) 