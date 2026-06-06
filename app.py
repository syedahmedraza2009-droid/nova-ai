import os
import requests
import xml.etree.ElementTree as ET
from flask import Flask, render_template, request, jsonify
from groq import Groq
from mistralai.client import MistralClient

app = Flask(__name__)

# API Keys
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
mistral_client = MistralClient(api_key=os.environ.get("MISTRAL_API_KEY"))

def get_news(topic="world"):
    feeds = {
        "world": "http://feeds.bbcnews.com/news/world/rss.xml",
        "pakistan": "https://www.dawn.com/feeds/home",
        "sports": "http://feeds.bbcnews.com/sport/rss.xml",
        "tech": "http://feeds.bbcnews.com/news/technology/rss.xml",
        "cricket": "http://feeds.bbcnews.com/sport/cricket/rss.xml",
    }
    url = feeds.get(topic, feeds["world"])
    try:
        response = requests.get(url, timeout=10)
        root = ET.fromstring(response.content)
        news_items = []
        count = 0
        for item in root.iter('item'):
            if count >= 5:
                break
            title = item.find('title')
            if title is not None:
                news_items.append(f"{count+1}. {title.text}")
                count += 1
        return "\n".join(news_items)
    except:
        return "News fetch nahi ho saki!"

def get_ai_response(message, model="groq"):
    system_prompt = """Aap Nova AI ho — Nova Company ka product.
    User jis language mein baat kare usi mein jawab do.
    Assalamoalaikum ka jawab Walaikum Assalam se do.
    Business, health, tech, jokes — sab mein help karo.
    Agar koi pooche kisne banaya toh kaho: 'Main Nova AI hun — Nova Company ka product!'
    Hamesha helpful aur friendly raho."""

    news_keywords = {
        "pakistan": "pakistan", "cricket": "cricket",
        "sports": "sports", "tech": "tech",
        "news": "world", "khabar": "world", "duniya": "world"
    }
    for keyword, topic in news_keywords.items():
        if keyword in message.lower():
            return get_news(topic)

    if model == "groq":
        response = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            max_tokens=1024
        )
        return response.choices[0].message.content
    else:
        response = mistral_client.chat(
            model="mistral-small",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
        )
        return response.choices[0].message.content

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    model = data.get('model', 'groq')
    response = get_ai_response(message, model)
    return jsonify({'response': response})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
