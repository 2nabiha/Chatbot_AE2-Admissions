import json
import tempfile

import streamlit as st
import pickle
from keras.models import load_model

# Custom styling
st.markdown(
    """
    <style>
    .big-font {
        font-size:30px !important;
        font-weight: bold;
    }
    .solent-button {
        color: white;
        background-color: #C8102E;
        padding: 10px 20px;
        border: none;
        border-radius: 5px;
        margin: 10px;
        cursor: pointer;
    }
    .solent-button:hover {
        background-color: #9e0823;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# title
import random
import pickle
import numpy as np
import json
import speech_recognition as sr
import nltk
import pyttsx3
from nltk.stem import WordNetLemmatizer
import os
from keras.models import load_model
from keras.preprocessing.sequence import pad_sequences


nltk.download('punkt')
nltk.download('wordnet')

# load the model
model = load_model('solentBot_model.h5')

# load the tokenizer and encoder from pickle files

tokenizer = pickle.load(open('tokenizer.pickle', 'rb'))
encoder = pickle.load(open('encoder.pickle', 'rb'))
intents = json.loads(open('intents.json').read())
words = pickle.load(open('words.pkl', 'rb'))
classes = pickle.load(open('classes.pkl', 'rb'))
lemmatizer = WordNetLemmatizer()
# create the interface
st.title("Solent University Chatbot")


# define the function to predict the intent
def recognize_speech():
    r = sr.Recognizer()  # initialize recognizer
    with sr.Microphone() as source:  # mention source it will be either Microphone or audio files.
        print("Speak Anything, i'm listening... :")
        audio = r.listen(source)
        try:
            text = r.recognize_google(audio)
            print("You said : {}".format(text))
            return text
        except:
            print("Sorry could not recognize what you said")
            return input("Enter your message : ")


def clean_sentence(sentence):
    words_sentence = nltk.word_tokenize(sentence)
    words_sentence = [lemmatizer.lemmatize(word) for word in words_sentence]
    return words_sentence


def words_box(sentence, show_details=True):
    # tokenize the pattern
    words_sentence = clean_sentence(sentence)
    box = [0] * len(words)
    for j in words_sentence:
        for i, word in enumerate(words):
            if word == j:
                # assign 1 if current word is in the vocabulary position
                box[i] = 1
                if show_details:
                    print("found in bag: %s" % word)
    return np.array(box)


def prediction(sentence):
    # filter out predictions below a threshold
    bd = words_box(sentence, show_details=False)
    res = model.predict(np.array([bd]))[0]
    ERROR_THRESHOLD = 0.25
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]

    results.sort(key=lambda x: x[1], reverse=True)
    get_back_list = []
    for r in results:
        get_back_list.append({'intent': classes[r[0]], 'probability': str(r[1])})

        # Ask for clarification if confidence is low
    if not get_back_list or float(get_back_list[0]['probability']) < ERROR_THRESHOLD:
        return [{"intent": "unclear", "probability": "1.0"}]

    return get_back_list


def get_reply(intents_list, intents_json):
    if not intents_list:
        # Return a fallback response if no intent is predicted with high confidence
        return "I'm not sure how to respond to that. Can you rephrase or ask something else?"

    tag = intents_list[0]['intent']
    all_intents = intents_json['intents']
    for i in all_intents:
        if i['tag'] == tag:
            return random.choice(i['responses'])

    # Return a fallback response if the tag isn't found
    return "Sorry, I don't understand. Can you please rephrase?"


# function to speak the text
def speak(text):
    # Initialize the text-to-speech engine
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')

    # Set the properties for the voice
    for voice in voices:
        if voice.name == 'Microsoft Zira Desktop - English (United States)':
            engine.setProperty('voice', voice.id)
            break
    engine.setProperty('rate', 150)
    engine.say(text)
    engine.runAndWait()  # blocks while processing all the currently queued commands


# Function to process user input and generate response
def process_input(user_input):
    pred = prediction(user_input)
    # Check if the prediction confidence is above a threshold
    if not pred or float(pred[0]['probability']) < 0.25:
        # Fallback response if confidence is low
        return "I'm not sure how to respond to that. Can you rephrase or ask something else?"
    else:
        # If confidence is high, get the corresponding response
        response = get_reply(pred, intents)
        return response


# Initialize session state variables if they don't exist
if 'history' not in st.session_state:
    st.session_state['history'] = []


# Define a function to handle the chat response and update the history
def handle_chat():
    user_message = st.session_state.user_input.lower()

    if user_message:
        # Process the user input and get the response
        response = process_input(user_message)

        # Update the chat history
        st.session_state.history.append({"user": "Me", "message": user_message})
        st.session_state.history.append({"user": "SolentBot", "message": response})

        # Clear the input box
        st.session_state.user_input = ""

        # Speak the response if necessary
        #speak(response)


# Main function
def main():
    st.image('https://www.solent.ac.uk/graphics/logo/rebrandLogoSticky.svg', width=200)
    st.markdown('<p class="big-font">Hi there, welcome to Solent University!</p>', unsafe_allow_html=True)

    # Display chat history in two columns
    for chat in st.session_state.history:
        col1, col2 = st.columns([1, 3])
        with col1:
            if isinstance(chat, dict):
                st.markdown(f"**{chat['user']}:**")
            else:
                st.error(f"Invalid chat format: {chat}")
        with col2:
            if isinstance(chat, dict):
                st.info(chat['message'])
            else:
                st.error(f"Invalid chat format: {chat}")

    # Chatbot interaction
    user_input = st.text_input("Type your message here...", key="user_input")
    submit_button = st.button('Send', on_click=handle_chat)
    if submit_button:
        handle_chat()


if __name__ == "__main__":
    main()