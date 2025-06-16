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
    
    def generate_conversation(self, topic, num_exchanges=7):
        """
        Generate a conversation dialogue based on a given topic using Gemini.
        
        Args:
            topic (str): The conversation topic (e.g., "Independence Day holiday")
            num_exchanges (int): Number of exchanges in the conversation
            
        Returns:
            list: List of dialogue exchanges with bot and user parts
        """
        
        prompt = f"""You are an English conversation teacher. Create a natural dialogue between two people about "{topic}". 
The dialogue should be appropriate for English language learners.

Create a {num_exchanges}-exchange conversation where:
- The first speaker (bot) starts the conversation
- Then it alternates with what the user should respond
- Each exchange builds naturally on the previous one
- Keep responses at intermediate English level - not too simple, not too complex
- Make the conversation engaging and educational

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
            return self._get_fallback_conversation(topic, num_exchanges)
    
    def _get_fallback_conversation(self, topic, num_exchanges=7):
        """
        Provide a fallback conversation if Gemini generation fails.
        """
        fallback_conversations = {
            "independence day holiday": [
                {
                    "exchange_number": 1,
                    "bot_says": "Hi! How did you celebrate Independence Day this year?",
                    "user_should_say": "I went to see fireworks with my family and friends."
                },
                {
                    "exchange_number": 2,
                    "bot_says": "That sounds fun! What's your favorite thing about the fireworks?",
                    "user_should_say": "I love the colorful explosions and the loud sounds they make."
                },
                {
                    "exchange_number": 3,
                    "bot_says": "Did you have a barbecue or picnic as well?",
                    "user_should_say": "Yes, we grilled hamburgers and hot dogs in the park."
                },
                {
                    "exchange_number": 4,
                    "bot_says": "What other activities did you do during the day?",
                    "user_should_say": "We played games and listened to patriotic music."
                },
                {
                    "exchange_number": 5,
                    "bot_says": "Do you know why we celebrate Independence Day?",
                    "user_should_say": "Yes, it's when America declared independence from Britain in 1776."
                },
                {
                    "exchange_number": 6,
                    "bot_says": "That's right! What does freedom mean to you personally?",
                    "user_should_say": "Freedom means being able to make my own choices and express my opinions."
                },
                {
                    "exchange_number": 7,
                    "bot_says": "That's a great perspective! Will you celebrate the same way next year?",
                    "user_should_say": "I hope so! It's become a wonderful family tradition for us."
                }
            ],
            "favorite food": [
                {
                    "exchange_number": 1,
                    "bot_says": "What's your favorite food?",
                    "user_should_say": "I really love pizza! It's my absolute favorite."
                },
                {
                    "exchange_number": 2,
                    "bot_says": "Pizza is delicious! What kind of toppings do you like?",
                    "user_should_say": "I prefer pepperoni and mushrooms with extra cheese."
                },
                {
                    "exchange_number": 3,
                    "bot_says": "That sounds tasty! Do you make pizza at home or order it?",
                    "user_should_say": "I usually order from my local pizzeria, but sometimes I make it myself."
                },
                {
                    "exchange_number": 4,
                    "bot_says": "Making pizza at home can be fun! What's the hardest part?",
                    "user_should_say": "Getting the dough just right is always challenging for me."
                },
                {
                    "exchange_number": 5,
                    "bot_says": "Have you tried any unusual pizza toppings?",
                    "user_should_say": "Once I tried pineapple on pizza, but I didn't really like it."
                },
                {
                    "exchange_number": 6,
                    "bot_says": "Pineapple on pizza is controversial! What other foods do you enjoy?",
                    "user_should_say": "I also love pasta and Chinese food, especially fried rice."
                },
                {
                    "exchange_number": 7,
                    "bot_says": "You have great taste in food! Do you cook often?",
                    "user_should_say": "I try to cook at least a few times a week to save money."
                }
            ],
            "travel experiences": [
                {
                    "exchange_number": 1,
                    "bot_says": "Have you traveled anywhere interesting recently?",
                    "user_should_say": "Yes, I visited Paris last summer and it was amazing!"
                },
                {
                    "exchange_number": 2,
                    "bot_says": "Paris sounds wonderful! What was your favorite part?",
                    "user_should_say": "I loved seeing the Eiffel Tower and walking along the Seine River."
                },
                {
                    "exchange_number": 3,
                    "bot_says": "Did you try any French food while you were there?",
                    "user_should_say": "Yes! I had croissants every morning and tried escargot for dinner."
                },
                {
                    "exchange_number": 4,
                    "bot_says": "How was the escargot? Many people are nervous to try it.",
                    "user_should_say": "It was actually quite good! The garlic butter made it taste delicious."
                },
                {
                    "exchange_number": 5,
                    "bot_says": "What was the biggest challenge during your trip?",
                    "user_should_say": "The language barrier was difficult since I don't speak much French."
                },
                {
                    "exchange_number": 6,
                    "bot_says": "Did you manage to communicate anyway?",
                    "user_should_say": "Most people spoke some English, and I used translation apps on my phone."
                },
                {
                    "exchange_number": 7,
                    "bot_says": "Would you like to visit France again or try somewhere new?",
                    "user_should_say": "I'd love to go back to France, but I also want to visit Italy next."
                }
            ]
        }
        
        # Try to find a matching fallback, otherwise create a generic one
        topic_key = topic.lower()
        if topic_key in fallback_conversations:
            return fallback_conversations[topic_key][:num_exchanges]
        
        # Generic fallback based on topic
        generic_exchanges = []
        for i in range(num_exchanges):
            if i == 0:
                bot_says = f"Let's talk about {topic}. What do you think about it?"
                user_says = f"I think {topic} is very interesting and important to me."
            elif i == 1:
                bot_says = f"That's great! Can you tell me more about your experience with {topic}?"
                user_says = f"I have some experience with {topic} and I find it quite enjoyable."
            elif i == 2:
                bot_says = f"What's the most interesting thing about {topic} for you?"
                user_says = f"The most interesting thing is how it affects my daily life."
            elif i == 3:
                bot_says = f"Have you learned anything new about {topic} recently?"
                user_says = f"Yes, I've been learning more about it through books and online."
            elif i == 4:
                bot_says = f"Do you think {topic} is important for other people too?"
                user_says = f"Absolutely! I think everyone can benefit from understanding {topic}."
            elif i == 5:
                bot_says = f"What advice would you give to someone new to {topic}?"
                user_says = f"I'd tell them to start slowly and be patient with themselves."
            else:
                bot_says = f"Thank you for sharing your thoughts about {topic}!"
                user_says = f"Thank you for the interesting conversation about {topic}!"
            
            generic_exchanges.append({
                "exchange_number": i + 1,
                "bot_says": bot_says,
                "user_should_say": user_says
            })
        
        return generic_exchanges 