import pyttsx3
import speech_recognition as sr
import wikipedia
import webbrowser
import requests
from bs4 import BeautifulSoup
import random
import os
import cv2
import numpy as np
import math

# Initialize the conversation history as an empty dictionary
conversation_history = {}


# Directory to store conversation history files
history_directory = "conversation_history"

# Ensure the history directory exists
os.makedirs(history_directory, exist_ok=True)

cap = cv2.VideoCapture(0)


# Function to save a question and response to a file
def save_to_file(question, response):
    # Limit the filename length to avoid issues
    filename = os.path.join(history_directory, f"{question[:50]}.txt")
    
    # Save the question and response to the file
    with open(filename, "w") as file:
        file.write(question + "\n")
        file.write(response + "\n")

def check_camera():
    global cap
    ret, frame = cap.read()

    if ret:
        speak("How many fingers am I holding up?")
        user_input = listen()
        
        if "one" in user_input:
            finger_count = count_fingers(frame)
            speak(f"I can see you holding up {finger_count} fingers.")
        else:
            speak("I couldn't understand the number of fingers.")
    else:
        speak("I'm sorry, I couldn't access the camera.")
        
        
def count_fingers(frame):
    # Convert the frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Perform edge detection
    edged = cv2.Canny(blurred, 50, 150)

    # Find contours in the edge map
    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if len(contours) == 0:
        return 0  # No fingers detected

    # Find the largest contour, which is typically the hand
    max_contour = max(contours, key=cv2.contourArea)

    # Calculate the convex hull of the hand
    hull = cv2.convexHull(max_contour, returnPoints=False)

    # Calculate the defects of the convex hull
    defects = cv2.convexityDefects(max_contour, hull)

    if defects is None:
        return 0  # No fingers detected

    # Count the number of finger defects
    finger_count = 0
    for defect in defects:
        s, e, f, d = defect[0]
        start = tuple(max_contour[s][0])
        end = tuple(max_contour[e][0])
        far = tuple(max_contour[f][0])

        # Use cosine rule to find the angle of the far point from the start and end points
        a = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
        b = math.sqrt((far[0] - start[0])**2 + (far[1] - start[1])**2)
        c = math.sqrt((end[0] - far[0])**2 + (end[1] - far[1])**2)
        angle = math.acos((b**2 + c**2 - a**2) / (2 * b * c))

        # If the angle is less than 90 degrees, it's a finger
        if angle < math.pi / 2:
            finger_count += 1

    return finger_count

def play_youtube(query):
    try:
        query = query.replace("play", "").strip()
        query = query.replace("on YouTube", "").strip()
        url = f"https://www.youtube.com/results?search_query={query}"
        webbrowser.open(url)
        speak(f"Opening YouTube and searching for '{query}'. Enjoy your video!")
    except Exception as e:
        speak("Sorry, I encountered an error while trying to play the video.")


# List of jokes
jokes = [
    "Why did the scarecrow win an award? Because he was outstanding in his field!",
    "Parallel lines have so much in common. It's a shame they'll never meet.",
    "I told my wife she was drawing her eyebrows too high. She looked surprised.",
    "Why don't skeletons fight each other? They don't have the guts.",
    "Did you hear about the mathematician who's afraid of negative numbers? He'll stop at nothing to avoid them.",
    "I'm reading a book on anti-gravity. It's impossible to put down!",
    "I used to play piano by ear, but now I use my hands.",
    "Why don't scientists trust atoms? Because they make up everything.",
    "I'm on a seafood diet. I see food, and I eat it.",
    "I told my wife she was bad at math. Now she's seeing a therapist.",
    "What do you call a fish with no eyes? Fsh.",
    "I used to be a baker, but I couldn't make enough dough.",
    "I'm reading a book about anti-gravity. It's really uplifting!",
    "Why did the bicycle fall over? Because it was two-tired.",
    "Parallel lines have so much in common. It's a shame they'll never meet.",
]

def tell_joke():
    # Randomly select a joke from the list
    random_joke = random.choice(jokes)
    speak(random_joke)
    
    
# Function to handle web search
def search_and_read_results(query):
    try:
        url = f"https://www.google.com/search?q={query}"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        search_results = soup.find_all("div", class_="tF2Cxc")
        
        if search_results:
            result_text = search_results[0].get_text()
            speak(result_text)
        else:
            speak("No information found on Chrome. Let's check Wikipedia.")
            wikipedia_result = search_wikipedia(query)
            speak(wikipedia_result)
    except requests.RequestException:
        speak("Sorry, I'm having trouble accessing the web right now. Please check your internet connection.")


responses = {
    "tell me a joke": tell_joke,
    "what's your name": "I'm Gideon, your personal assistant.",
    "who are you": "I'm Gideon, your personal assistant.",
    "how are you": "I'm just a computer program, but I'm here to assist you!",
    "search the web for": search_and_read_results,
    "open YouTube and play": play_youtube, 

}



def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=1)  
        audio = recognizer.listen(source, timeout=900)  

        try:
            user_input = recognizer.recognize_google(audio)
            print("You said:", user_input)
            return user_input.lower()
        except sr.UnknownValueError:
            print("Sorry, could not understand audio.")
            return ""
        except sr.WaitTimeoutError:
            print("Listening timed out.")
            return ""

# Function to add a question and response to the conversation history
def add_to_history(question, response):
    conversation_history[question] = response
    

def load_history():
    global conversation_history
    for filename in os.listdir(history_directory):
        if filename.endswith(".txt"):
            with open(os.path.join(history_directory, filename), "r") as file:
                lines = file.readlines()
                question = lines[0].strip()
                response = lines[1].strip()
                conversation_history[question] = response

# Function to show the conversation history
def show_history():
    if conversation_history:
        for question, response in conversation_history.items():
            print(f"Q: {question}")
            print(f"A: {response}")
    else:
        print("Conversation history is empty.")

def speak(response):
    engine = pyttsx3.init()
    engine.say(response)
    engine.runAndWait()

def search_wikipedia(query):
    try:
        result = wikipedia.summary(query, sentences=2)
        return result
    except wikipedia.exceptions.DisambiguationError as e:
        return f"Multiple options found. Can you be more specific?"
    except wikipedia.exceptions.PageError as e:
        return f"Sorry, I couldn't find any information on {query}."
    except Exception as e:
        return f"Sorry, an error occurred while searching Wikipedia."

def search_on_chrome(query):
    try:
        url = f"https://www.google.com/search?q={query}"
        webbrowser.open(url)
    except Exception as e:
        return f"Sorry, an error occurred while opening the browser."




def main():
    try:
        is_sleeping = False
        speak("Hello! I'm Gideon, your personal assistant. How can I assist you today?")

        while True:
            if not is_sleeping:
                user_input = listen()
                if user_input == "exit":
                    speak("Goodbye!")
                    break

                # Convert user input to lowercase for case-insensitive comparison
                user_input_lower = user_input.lower()

                if user_input_lower in conversation_history:
                    response = conversation_history[user_input_lower]
                    speak(response)
                else:
                    if "how do you think" in user_input_lower and "in 5 years" in user_input_lower:
                        response = "I believe the world will continue to advance in technology and innovation over the next five years, with significant developments in areas like artificial intelligence, renewable energy, and healthcare."
                        speak(response)
                        add_to_history(user_input_lower, response)
                        save_to_file(user_input_lower, response)
                    elif "search the web for" in user_input_lower:
                        query = user_input_lower.replace("search the web for", "").strip()
                        search_and_read_results(query)
                    elif "show history" in user_input_lower:
                        show_history()
                    elif "sleep" in user_input_lower:
                        speak("Okay, I'm going to sleep. Wake me up when you're ready.")
                        is_sleeping = True
                    elif "can you hear me" in user_input_lower:
                        speak("Yes, I can hear you.")
                    elif "open youtube and play" in user_input_lower:  # Updated for case-insensitivity
                        query = user_input_lower.replace("open youtube and play", "").strip()
                        play_youtube(query)
                    else:
                        handled = False
                        for key, response in responses.items():
                            if key.lower() in user_input_lower:
                                if callable(response):
                                    response()
                                else:
                                    speak(response)
                                handled = True
                                break

                        if not handled:
                            speak("I'm not sure how to respond to that. Please ask another question.")
                        add_to_history(user_input_lower, "I'm not sure how to respond to that. Please ask another question.")
                        save_to_file(user_input_lower, "I'm not sure how to respond to that. Please ask another question.")
            else:
                activation_phrase = listen()
                if activation_phrase == "wake up":
                    speak("I'm awake and ready to assist you.")
                    is_sleeping = False
                elif activation_phrase == "exit":
                    speak("Goodbye!")
                    break
    except sr.RequestError:
        speak("Sorry, I'm having trouble with speech recognition. Please check your microphone and try again.")
    except KeyboardInterrupt:
        speak("Goodbye!")
    except Exception as e:
        speak("Oops! Something went wrong. Please try again later.")
        print(e)


if __name__ == "__main__":
    main()