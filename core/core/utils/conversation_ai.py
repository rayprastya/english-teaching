import google.generativeai as genai
import json
import os
from django.conf import settings

class ConversationAI:
    def __init__(self):
        # Initialize Gemini client
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def generate_conversation(self, topic, num_exchanges=7, difficulty='medium'):
        """
        Generate a conversation dialogue based on a given topic using Gemini.
        
        Args:
            topic (str): The conversation topic (e.g., "Independence Day holiday")
            num_exchanges (int): Number of exchanges in the conversation
            difficulty (str): Difficulty level - 'easy', 'medium', or 'hard'
            
        Returns:
            list: List of dialogue exchanges with bot and user parts
        """
        
        # Customize prompt based on difficulty level
        difficulty_instructions = {
            'easy': {
                'level_description': 'beginner level',
                'vocabulary': 'simple, everyday vocabulary',
                'grammar': 'basic grammar structures',
                'topics': 'familiar, everyday topics',
                'sentence_length': 'short sentences (8-12 words)',
                'complexity': 'very simple concepts'
            },
            'medium': {
                'level_description': 'intermediate level',
                'vocabulary': 'varied vocabulary with some complex words',
                'grammar': 'mix of simple and complex grammar',
                'topics': 'diverse topics that require some thinking',
                'sentence_length': 'moderate length sentences (12-18 words)',
                'complexity': 'moderately complex ideas'
            },
            'hard': {
                'level_description': 'advanced level',
                'vocabulary': 'sophisticated vocabulary and expressions',
                'grammar': 'complex grammar structures and tenses',
                'topics': 'abstract or complex topics',
                'sentence_length': 'longer, more complex sentences (15-25 words)',
                'complexity': 'complex ideas and nuanced concepts'
            }
        }
        
        diff_config = difficulty_instructions.get(difficulty, difficulty_instructions['medium'])
        
        prompt = f"""You are an English conversation teacher. Create a natural dialogue between two people about "{topic}". 
The dialogue should be appropriate for {diff_config['level_description']} English language learners.

Difficulty Level: {difficulty.upper()}

Guidelines for {difficulty} level:
- Use {diff_config['vocabulary']}
- Apply {diff_config['grammar']}
- Focus on {diff_config['topics']}
- Keep responses to {diff_config['sentence_length']}
- Present {diff_config['complexity']}

Create a {num_exchanges}-exchange conversation where:
- The first speaker (bot) starts the conversation
- Then it alternates with what the user should respond
- Each exchange builds naturally on the previous one
- Make the conversation engaging and educational
- Ensure the difficulty level is consistent throughout

Format your response as a JSON array where each exchange has:
- "exchange_number": The number of this exchange (1, 2, 3, etc.)
- "bot_says": What the first speaker (bot) says
- "user_should_say": What the user should respond with

Example format:
[
    {{
        "exchange_number": 1,
        "bot_says": "Hi! I heard you celebrated Independence Day yesterday. How was it?",
        "user_should_say": "It was great! We had a barbecue with family and watched fireworks."
    }},
    {{
        "exchange_number": 2,
        "bot_says": "That sounds wonderful! What's your favorite part about Independence Day celebrations?",
        "user_should_say": "I love the fireworks display. The colors are so beautiful against the night sky."
    }}
]

Please respond with ONLY the JSON array, no additional text or formatting."""
        
        try:
            response = self.model.generate_content(prompt)
            
            # Parse the JSON response
            conversation_json = response.text.strip()
            
            # Remove any markdown formatting if present
            if conversation_json.startswith('```json'):
                conversation_json = conversation_json[7:]
            if conversation_json.endswith('```'):
                conversation_json = conversation_json[:-3]
            
            conversation_data = json.loads(conversation_json)
            
            # Validate the response structure
            if not isinstance(conversation_data, list):
                raise ValueError("Response is not a list")
            
            for exchange in conversation_data:
                if not all(key in exchange for key in ['exchange_number', 'bot_says', 'user_should_say']):
                    raise ValueError("Missing required keys in exchange")
            
            return conversation_data
            
        except Exception as e:
            print(f"Error generating conversation with Gemini: {str(e)}")
            # Return a fallback conversation if Gemini fails
            return self._get_fallback_conversation(topic, num_exchanges, difficulty)

    def _get_fallback_conversation(self, topic, num_exchanges=7, difficulty='medium'):
        """
        Fallback conversation generation if Gemini fails
        """
        fallback_conversations = {
            "independence day holiday": [
                {
                    "exchange_number": 1,
                    "bot_says": "Hi! I heard you celebrated Independence Day yesterday. How was it?",
                    "user_should_say": "It was great! We had a barbecue with family and watched fireworks."
                },
                {
                    "exchange_number": 2,
                    "bot_says": "That sounds wonderful! What's your favorite part about Independence Day celebrations?",
                    "user_should_say": "I love the fireworks display. The colors are so beautiful against the night sky."
                },
                {
                    "exchange_number": 3,
                    "bot_says": "Fireworks are amazing! Did you have any special food at your barbecue?",
                    "user_should_say": "Yes, we grilled burgers and hot dogs. My mom made her famous potato salad too."
                },
                {
                    "exchange_number": 4,
                    "bot_says": "That sounds delicious! Do you celebrate the same way every year?",
                    "user_should_say": "Pretty much. It's become a family tradition that we all look forward to."
                },
                {
                    "exchange_number": 5,
                    "bot_says": "Family traditions are so important. What does Independence Day mean to you?",
                    "user_should_say": "It's a time to appreciate our freedom and spend time with loved ones."
                },
                {
                    "exchange_number": 6,
                    "bot_says": "That's a beautiful way to think about it. Did you watch any parades?",
                    "user_should_say": "Yes, we went to the local parade in the morning. The marching band was fantastic."
                },
                {
                    "exchange_number": 7,
                    "bot_says": "Parades are such a great part of the celebration. Are you already planning for next year?",
                    "user_should_say": "Absolutely! We're thinking about inviting more friends and family."
                }
            ],
            "favorite food": [
                {
                    "exchange_number": 1,
                    "bot_says": "What's your favorite food?",
                    "user_should_say": "I love pizza! It's my favorite food of all time."
                },
                {
                    "exchange_number": 2,
                    "bot_says": "Pizza is great! What kind of pizza do you like best?",
                    "user_should_say": "I prefer pepperoni pizza with extra cheese."
                },
                {
                    "exchange_number": 3,
                    "bot_says": "That's a classic choice! Do you make pizza at home or order it?",
                    "user_should_say": "I usually order it from my favorite pizza place downtown."
                },
                {
                    "exchange_number": 4,
                    "bot_says": "Nice! How often do you eat pizza?",
                    "user_should_say": "Maybe once or twice a week. I try not to eat too much."
                },
                {
                    "exchange_number": 5,
                    "bot_says": "That's probably a good idea. Have you ever tried making pizza yourself?",
                    "user_should_say": "Yes, I tried it once but it was much harder than I expected."
                },
                {
                    "exchange_number": 6,
                    "bot_says": "Homemade pizza can be tricky. What was the most difficult part?",
                    "user_should_say": "Getting the dough right was really challenging for me."
                },
                {
                    "exchange_number": 7,
                    "bot_says": "The dough is definitely the hardest part. Would you try making it again?",
                    "user_should_say": "Maybe someday, but for now I'll stick to ordering it!"
                }
            ],
            "travel experiences": [
                {
                    "exchange_number": 1,
                    "bot_says": "Have you traveled anywhere interesting recently?",
                    "user_should_say": "Yes, I went to France last month for two weeks."
                },
                {
                    "exchange_number": 2,
                    "bot_says": "France sounds amazing! What was your favorite city there?",
                    "user_should_say": "I loved Paris the most. The architecture was incredible."
                },
                {
                    "exchange_number": 3,
                    "bot_says": "Paris is beautiful! Did you visit any famous landmarks?",
                    "user_should_say": "Yes, I went to the Eiffel Tower and the Louvre Museum."
                },
                {
                    "exchange_number": 4,
                    "bot_says": "Those are must-see places! How was the food?",
                    "user_should_say": "The food was fantastic. I tried so many different pastries and wines."
                },
                {
                    "exchange_number": 5,
                    "bot_says": "French cuisine is world-famous. Did you try to speak French while you were there?",
                    "user_should_say": "I tried my best, but most people spoke English with me."
                },
                {
                    "exchange_number": 6,
                    "bot_says": "That's still great that you tried! What was the highlight of your trip?",
                    "user_should_say": "Probably watching the sunset from the Eiffel Tower. It was magical."
                },
                {
                    "exchange_number": 7,
                    "bot_says": "That sounds like a perfect moment. Would you like to visit France again?",
                    "user_should_say": "Definitely! I want to explore more of the countryside next time."
                }
            ]
        }
        
        # Adjust for difficulty level
        topic_key = topic.lower()
        if topic_key in fallback_conversations:
            base_conversation = fallback_conversations[topic_key][:num_exchanges]
            return self._adjust_conversation_for_difficulty(base_conversation, difficulty)
        
        # Generic fallback based on topic and difficulty
        return self._generate_generic_fallback(topic, num_exchanges, difficulty)
        
    def _adjust_conversation_for_difficulty(self, conversation, difficulty):
        """Adjust conversation complexity based on difficulty level"""
        # For now, return as is - can be enhanced to simplify/complexify language
        return conversation
        
    def _generate_generic_fallback(self, topic, num_exchanges, difficulty):
        """Generate a generic fallback conversation"""
        generic_exchanges = []
        
        # Difficulty-based templates
        if difficulty == 'easy':
            templates = [
                ("Let's talk about {topic}. Do you like it?", "Yes, I think {topic} is very good."),
                ("Can you tell me more about {topic}?", "I think {topic} is important in my life."),
                ("What do you think about {topic}?", "I like {topic} because it makes me happy."),
                ("Do you know much about {topic}?", "I know a little bit about {topic}."),
                ("Is {topic} popular in your country?", "Yes, {topic} is very popular here."),
            ]
        elif difficulty == 'medium':
            templates = [
                ("Let's discuss {topic}. What's your experience with it?", "I have some experience with {topic} and find it quite interesting."),
                ("Can you share your thoughts on {topic}?", "I think {topic} plays an important role in modern society."),
                ("What's the most interesting aspect of {topic} for you?", "The most fascinating thing about {topic} is how it affects daily life."),
                ("Have you learned anything new about {topic} recently?", "I've been exploring {topic} through various books and online resources."),
                ("How do you think {topic} will change in the future?", "I believe {topic} will continue to evolve and become more important."),
            ]
        else:  # hard
            templates = [
                ("I'd like to explore your perspective on {topic}. What are your thoughts?", "I find {topic} to be a multifaceted subject that requires careful consideration."),
                ("Can you analyze the impact of {topic} on society?", "The implications of {topic} are far-reaching and affect various aspects of our lives."),
                ("What are the main challenges associated with {topic}?", "The primary obstacles related to {topic} include complexity and accessibility issues."),
                ("How would you evaluate the current state of {topic}?", "The contemporary landscape of {topic} presents both opportunities and challenges."),
                ("What predictions would you make about the future of {topic}?", "I anticipate that {topic} will undergo significant transformations in the coming years."),
            ]
        
        for i in range(min(num_exchanges, len(templates))):
            bot_says, user_says = templates[i]
            generic_exchanges.append({
                "exchange_number": i + 1,
                "bot_says": bot_says.format(topic=topic),
                "user_should_say": user_says.format(topic=topic)
            })
        
        return generic_exchanges 