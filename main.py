import requests
import json
import os
import webbrowser
from dotenv import load_dotenv

load_dotenv()

current_api_key = os.getenv('OPENROUTER_API_KEY', '').strip()

# User profile tracking
user_profile = {
    "type": "general",  # general, beginner, expert, student, professional
    "interests": [],
    "previous_questions": []
}

# Custom responses with multiple options based on user type
custom_responses = {
    "what is your name": {
        "general": "I am alpha AI, your helpful assistant.",
        "beginner": "Hi! I'm alpha AI, your friendly AI helper. I'm here to make things simple for you!",
        "expert": "I am alpha AI, an advanced language model designed for complex problem-solving and analysis.",
        "student": "Hello! I'm alpha AI, your study buddy. I can help you learn and understand concepts better.",
        "professional": "I am alpha AI, your professional AI assistant for business and technical tasks."
    },
    "what is python": {
        "general": "Python is a high-level programming language known for its simplicity and readability.",
        "beginner": "Python is like a friendly programming language that's easy to learn! It's great for beginners because it reads almost like English.",
        "expert": "Python is a dynamically-typed, interpreted high-level language with extensive libraries for data science, web development, and automation.",
        "student": "Python is a programming language perfect for learning! It's used in schools because it's easy to understand and has many applications.",
        "professional": "Python is a versatile programming language widely used in enterprise applications, data analysis, machine learning, and web development."
    },
    "hello": {
        "general": "Hello! How can I help you today?",
        "beginner": "Hi there! Welcome! Don't worry if you're new to this - I'll explain everything clearly.",
        "expert": "Hello. What technical challenge can I help you solve today?",
        "student": "Hey! Ready to learn something new? What topic interests you?",
        "professional": "Good day. How can I assist you with your work today?"
    },
    "hi": {
        "general": "Hi there! What would you like to know?",
        "beginner": "Hi! I'm excited to help you learn! What would you like to explore?",
        "expert": "Hi. What complex problem are we tackling today?",
        "student": "Hi! Let's dive into some learning. What subject are you working on?",
        "professional": "Hi. What business or technical task can I help you with?"
    }
}

# Initialize DeepSeek via OpenRouter API
def call_deepseek_api(question, api_key: str):
    url = "https://openrouter.ai/api/v1/chat/completions"
    if not api_key:
        return {"error": "Missing API key. Type ChAnGe to set it."}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": "deepseek/deepseek-chat",
        "messages": [
            {"role": "user", "content": f"Question: {question}\nAnswer:"}
        ],
        "temperature": 0.7,
        "max_tokens": 256
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code != 200:
        print(f"API Error: {response.status_code}")
        print(f"Response: {response.text}")
        return {"error": f"HTTP {response.status_code}"}
    
    return response.json()

def _mask_key(key: str) -> str:
    if not key:
        return "(not set)"
    if len(key) <= 8:
        return "*" * len(key)
    return f"{key[:4]}...{key[-4:]}"

def detect_user_type(question):
    """Simple user type detection based on question patterns"""
    question_lower = question.lower()
    
    # Beginner indicators
    beginner_words = ["what is", "how do i", "explain", "simple", "easy", "beginner", "new to", "don't understand"]
    if any(word in question_lower for word in beginner_words):
        return "beginner"
    
    # Expert indicators  
    expert_words = ["algorithm", "optimization", "architecture", "implementation", "performance", "scalability", "enterprise"]
    if any(word in question_lower for word in expert_words):
        return "expert"
    
    # Student indicators
    student_words = ["homework", "assignment", "study", "exam", "course", "learn", "tutorial", "practice"]
    if any(word in question_lower for word in student_words):
        return "student"
    
    # Professional indicators
    professional_words = ["business", "project", "team", "meeting", "deadline", "client", "budget", "strategy"]
    if any(word in question_lower for word in professional_words):
        return "professional"
    
    return "general"

def get_custom_response(question):
    """Get appropriate response based on user type"""
    question_lower = question.lower()
    
    if question_lower in custom_responses:
        responses = custom_responses[question_lower]
        if isinstance(responses, dict):
            # Multiple responses available - choose based on user type
            user_type = user_profile["type"]
            if user_type in responses:
                return responses[user_type]
            else:
                return responses.get("general", "I don't have a specific response for that.")
        else:
            # Single response (backward compatibility)
            return responses
    
    return None

# Interactive chat loop
print("Alpha AI Chat - Type 'quit' to exit | Type 'ChAnGe' to set API key | Type 'TeAcH' to add custom responses | Type 'PrOfIlE' to set user type | Type 'WeAtHeR' for weather")
print("-" * 40)

while True:
    question = input("\nYou: ").strip()
    
    if question.lower() in ['quit', 'exit', 'bye']:
        print("Goodbye!")
        break
    
    if question == 'ChAnGe':
        new_key = input("Enter new OpenRouter API key: ").strip()
        if new_key:
            current_api_key = new_key
            print("API key updated.")
        else:
            print("No key entered. API key not changed.")
        continue
    
    if question == 'StAtUs':
        print(f"Current API key: {_mask_key(current_api_key)}")
        probe = call_deepseek_api("ping", current_api_key)
        if "choices" in probe:
            print("Status: key appears valid.")
        else:
            print(f"Status: key may be invalid. Error: {probe.get('error', 'Unknown error')}")
        continue
    
    if question == 'TeAcH':
        print("Teaching mode - Add custom responses")
        print("Available user types: general, beginner, expert, student, professional")
        user_type = input("Enter user type (required): ").strip().lower()
        
        if user_type not in ["general", "beginner", "expert", "student", "professional"]:
            print("Invalid user type. Please choose from: general, beginner, expert, student, professional")
            continue
            
        teach_question = input("Enter the question: ").strip().lower()
        if teach_question:
            teach_answer = input("Enter the answer: ").strip()
            if teach_answer:
                if teach_question not in custom_responses:
                    custom_responses[teach_question] = {}
                custom_responses[teach_question][user_type] = teach_answer
                print(f"Added: '{teach_question}' for {user_type} -> '{teach_answer}'")
                
                # Show all responses for this question if multiple exist
                if len(custom_responses[teach_question]) > 1:
                    print(f"All responses for '{teach_question}':")
                    for profile, response in custom_responses[teach_question].items():
                        print(f"  {profile}: {response}")
            else:
                print("No answer provided.")
        else:
            print("No question provided.")
        continue
    
    if question == 'PrOfIlE':
        print(f"Current profile: {user_profile}")
        print("Available types: general, beginner, expert, student, professional")
        new_type = input("Set your user type: ").strip().lower()
        if new_type in ["general", "beginner", "expert", "student", "professional"]:
            user_profile["type"] = new_type
            print(f"User type set to: {new_type}")
        else:
            print("Invalid user type.")
        continue
    
    if question == 'WeAtHeR':
        city = input("Enter city name: ").strip()
        if city:
            # Open weather website for the city
            weather_url = f"https://www.google.com/search?q=weather+{city.replace(' ', '+')}"
            try:
                webbrowser.open(weather_url)
                print(f"Alpha: Opening weather information for {city} in your browser...")
            except Exception as e:
                print(f"Alpha: Could not open browser. Please visit: {weather_url}")
        else:
            print("Alpha: No city provided.")
        continue
    
    if question.startswith('weather in '):
        city = question[len('weather in '):].strip()
        if city:
            weather_url = f"https://www.google.com/search?q=weather+{city.replace(' ', '+')}"
            try:
                webbrowser.open(weather_url)
                print(f"Alpha: Opening weather information for {city} in your browser...")
            except Exception as e:
                print(f"Alpha: Could not open browser. Please visit: {weather_url}")
        else:
            print("Alpha: Please specify a city, e.g., weather in London")
        continue
    
    if not question:
        print("Please enter a question.")
        continue
    
    # Update user profile based on question
    detected_type = detect_user_type(question)
    if detected_type != "general":
        user_profile["type"] = detected_type
    
    # Track previous questions
    user_profile["previous_questions"].append(question)
    if len(user_profile["previous_questions"]) > 10:  # Keep only last 10
        user_profile["previous_questions"] = user_profile["previous_questions"][-10:]
    
    # Check for custom responses first
    custom_response = get_custom_response(question)
    if custom_response:
        print("Alpha:", custom_response)
    else:
        print("Alpha: ", end="")
        result = call_deepseek_api(question, current_api_key)
        
        if "choices" in result:
            print(result["choices"][0]["message"]["content"])
        else:
            print("Error:", result.get("error", "Unknown error"))
