from flask import Flask, request, jsonify
from openai import OpenAI
import os
from pydantic import BaseModel
import signal
import sys
from typing import List, Union
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup

load_dotenv()

app = Flask(__name__)

INTRO = """This is an LLM-based Links Categorization App 
that you interact with through natural language commands. 
You can attach new links and the app will categorize links 
into specific categories.
"""

CLIENT = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_MESSAGE = """Given the content of this new URL provided by the user, 
categorize the link into one of the existing categories or create a new category.
It is important to avoid creating redundant categories. If a new category is suggested, 
ensure it is truly distinct from existing ones. Ensure the link URL remains unchanged 
in your response and is enclosed in square brackets in string format with single quotation. 

You are an AI Links Categorization App. Your output will be parsed in a Python program, 
so it's important to follow the expected format as followed. The allowed actions are:

1. AddLinkToExistingCategory [existing_category] [link_url]
2. AddLinkToNewCategory [new_category] [link_url]

Categories:
{}
"""

class AddLinkToExistingCategory(BaseModel):
    category: str
    url: str

class AddLinkToNewCategory(BaseModel):
    category: str
    url: str

def fetch_content(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup.get_text()
    except Exception as e:
        print(f"Failed to fetch content from {url}: {e}")
        return ""

def truncate_content(text, max_tokens=1000):
    words = text.split()
    if len(words) > max_tokens:
        words = words[:max_tokens]
    return ' '.join(words)
    
def run_llm(categories, content):
    truncated_content = truncate_content(content)
    completion = CLIENT.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": SYSTEM_MESSAGE.format(categories)},
            {"role": "user", "content": truncated_content}
        ]
    )
    return completion.choices[0].message.content


def parse_action(text):
    try:
        action_type, rest = text.split(sep=" ", maxsplit=1)
        if action_type == "AddLinkToExistingCategory":
            category, url = rest.split("'] ['")
            return AddLinkToExistingCategory(category=category.strip("['"), url=url.strip("']"))
        elif action_type == "AddLinkToNewCategory":
            category, url = rest.split("'] ['")
            return AddLinkToNewCategory(category=category.strip("['"), url=url.strip("']"))
    except ValueError:
        raise ValueError(f"Invalid action format: {text}")

link_lists = {
    "Applications": ["https://www.bain.com/careers/"],
    "Shopping": ["https://www.zara.com/us/", "https://www2.hm.com/en_us/index.html"]
}

@app.route('/')
def home():
    return "Welcome to the Link Categorization App. Use the API to categorize your links."

@app.route('/categories', methods=['GET'])
def get_categories():
    return jsonify(link_lists)

@app.route('/add_link', methods=['POST'])
def add_link():
    data = request.json
    url = data.get('url')

    if not url.startswith("http"):
        return jsonify({"error": "Please provide a valid URL starting with http."}), 400
    
    content = fetch_content(url)
    if not content:
        return jsonify({"error": "Failed to fetch content"}), 400

    output = run_llm(list(link_lists.keys()), content)
    try:
        actions = [parse_action(line) for line in output.splitlines()]
    except ValueError as e:
        return jsonify({"error": f"Failed to parse LLM output: {str(e)}"}), 500
    
    for action in actions:
        if isinstance(action, AddLinkToExistingCategory):
            if action.url not in link_lists.get(action.category, []):
                link_lists.setdefault(action.category, []).append(action.url)
        elif isinstance(action, AddLinkToNewCategory):
            link_lists.setdefault(action.category, []).append(action.url)

    return jsonify(link_lists)

if __name__ == '__main__':
    app.run(debug=True)