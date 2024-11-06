import sys, os
import re
import time
import random
import numpy as np
from tqdm import tqdm
import json

## Setup
import openai

openai.api_key = '...'
client = openai.OpenAI(api_key=openai.api_key)

def call_openai_api(prompt,
                    *,
                    model_name="gpt-4o-mini",
                    system_prompt="You are a helpful assistant. Follow the instruction as closely as possible.",
                    temperature=0,
                    max_tokens=2048,
                    timeout_failure=1):
    while True:
        try:
            return openai.chat.completions.create(
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": (system_prompt)},
                    {"role": "user", "content": prompt},
                ],
            ).choices[0].message.content.strip()
        except Exception as e:
            print(e)
            time.sleep(timeout_failure)

## Define process functions
prompt_convert_to_json = """You will receive a user prompt about a vacation plan.
Your task is to convert this user prompt into Python dictionary format.

The dictionary needs to have the following keys:
"departure": city (if applicable), state (if applicable). State name is the two-letter code.
"destination": city (if applicable), state (if applicable). State name is the two-letter code.
"start_date": str,
"end_date": str,
"duration": str,
"budget": int,
"accommodation_requirements": List of str
"restaurant_requirements": List of str
"attration_requirements": List of str

If information regarding one key is missing, use value 0, '', or empty list to represent it depending on its data type.
Now, please do the task for the following user prompt. ONLY output the dictionary.

## User prompt
{}

## Dictionary format
"""
database = json.load(open("C:/Users/linhn/Desktop/CS1114/codefest/Source_code/database_aggregate_gpt4o_unified.json"))

def parse_user_prompt(user_prompt):
    output = call_openai_api(prompt=prompt_convert_to_json.format(user_prompt))
    output = '{' + output.split("```python\n", 1)[1].split("```", 1)[0].split('{', 1)[1]
    return json.loads(output)


def location_match(city, entry_location):
    if type(city) == list:
        for location in city:
            if location in entry_location:
                return True
    elif type(city) == str:
        if city in entry_location:
            return True
    else:
        return False


def scan_database(user_prompt_json, database):
    # flight and transportation
    departure_city = user_prompt_json["departure"]
    destination_city = user_prompt_json["destination"]

    flight_and_transportation = []
    for entry in database["flight_and_transportation"]:
        if (location_match(departure_city, entry["departure"]) and location_match(destination_city, entry["destination"])) or \
            (location_match(departure_city, entry["destination"]) and location_match(destination_city, entry["departure"])):  # departing and returning trip
            flight_and_transportation.append(entry)

    accommodation = []
    for entry in database["accommodation"]:
        if location_match(destination_city, entry["location"]):
            accommodation.append(entry)

    attraction = []
    for entry in database["attraction"]:
        if location_match(destination_city, entry["location"]):
            attraction.append(entry)

    restaurant = []
    for entry in database["restaurant"]:
        if location_match(destination_city, entry["location"]):
            restaurant.append(entry)

    subdatabase = {
        "flight_and_transportation": flight_and_transportation,
        "accommodation": accommodation,
        "attraction": attraction,
        "restaurant": restaurant
    }

    return subdatabase


def query_database(user_prompt, database):
    while True:
        try:
            user_prompt_json = parse_user_prompt(user_prompt)
            # print(user_prompt_json)
            subdatabase = scan_database(user_prompt_json, database)
            break
        except Exception as e:
            print(e)
            time.sleep(1)
    return json.dumps(subdatabase, indent=4)


def griffin_travelplanner(user_prompt):
    subdatabase = query_database(user_prompt, database)
    prompt = (
        'Here is the database:'
        '{data}'
        'Based on the database in this file, which stores all information you use, {question}'
        'Please return in JSON format and detailed activities. '
        'Note that for each activity, you should provide the attribute (cost, time_begin, time_end, name, location, duration, description). '
        'Duplicate hotel and flight information to the trip attribute (departure_transportation, return_transportation). '
        'For the accommodations attribute, you should put the day you begin to stay and the day you end, with attribute (name, price, location, description, check_in, check_out, nights). '
        'Note that accommodation is a list and the attribute name should be accommodations. '
        'Remember to calculate the right number of nights staying in a hotel. Also, you should list all three meals in a day (breakfast, lunch, dinner). '
        'The itinerary attribute is under trip.'
    ).format(question=user_prompt, data=subdatabase)
    response = openai.chat.completions.create(
        model='gpt-4o',
        temperature=0,
        max_tokens=8192,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant. Answer as concisely as possible."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    )
    message = response.choices[0].message.content
    output = re.findall(r'```json\n(.*?)\n```', message, flags=re.DOTALL)[0]
    return json.loads(output)


def demo():
    user_prompt = "Could you please arrange a 3-day trip for two, starting in Sacramento and heading to Atlanta, from March 14th to March 16th, 2022. The budget for this trip is $4,700, and we require accommodations where parties are allowed."
    plan =  griffin_travelplanner(user_prompt=user_prompt,
                          database=database)

    print(plan)


if __name__ == "__main__":
    demo()
