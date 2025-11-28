from openai import OpenAI
from dotenv import load_dotenv
import requests
import json

from pydantic import BaseModel, Field


client = OpenAI(
    api_key="AIzaSyBk5E_AtNB56MT9BDHtz2T4D5LGy5TR1y8",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

SYSTEM_PROMPT = """
    You're an exprert AI assistant in resolving user queries using chain of thougt process.
    You work on START, PLAN and OUTPUT steps.
    You need to first PLAN what needs to be done. The PLAN can be multiple steps.
    Once you think enough PLAN has been done, finally you can give an OUTPUT.
    You can also call a tool form the list of available tools if require
    for every tool call wait for the observe step which is the output from the called tool

    Available Tools: 
    - get_weather: Takes city name as an input string and returns the weather information about the city


    Rules: 
    - Strictly follow the given JSON output format and return single json object only
    - Only run one step at a time.
    - The sequence of steps is START (where user gives an input), PLAN (that can be multiple times), OUTPUT

    Output JSON Format:
    {"step": "START | "PLAN" | "OUTPUT" | "TOOL" , "content":"string", "tool":"string", "input":"string"}


    Example 2:
    START: What is the weather of Delhi?
    PLAN:{"step":"PLAN", "content":"Seems like user is interested in getting weather of Delhi in India"}
    PLAN:{"step":"PLAN", "content":"lets see if we have any availble tools in the list of tools"}
    PLAN:{"step":"PLAN", "content":"Great we have get_weather tool available for this query"}
    PLAN:{"step":"PLAN", "content":"I need to call get_weather tool for delhi as input for city"}
    PLAN:{"step":"TOOL","tool":"get_weather", "input":"delhi"}
    PLAN:{"step":"OBSERVE","tool":"get_weather", "output":"the temp of delhi is couldy with 20 C"}
    PLAN:{"step":"PLAN","content":"Great I got the weather info about delhi"}
    OUTPUT: {"step": "OUTPUT", "content":"The current weather in delhi is 20 C with some couldy sky"}



    


"""

def get_weather(city : str):
    url = f"https://wttr.in/{city.lower()}?format=%C+%t"

    response = requests.get(url)

    if(response.status_code==200):
        return f"The weather in {city} is: {response.text} "

import re

def extract_json(text):
    # Find the FIRST JSON object using regex
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match:
        return None
    json_str = match.group(0)
    try:
        return json.loads(json_str)
    except:
        return None


available_tools = {
    "get_weather":get_weather,
    
}
def main():
    message_history = [{
        "role":"system", "content":SYSTEM_PROMPT
    }]
    user_query = input("> ")
    message_history.append({"role":"user", "content":user_query})
    while True:


        res  = client.chat.completions.create(
            model = "gemini-2.5-flash",
            response_format = {"type":"json_object"},
            messages=message_history
        )
        raw_result = res.choices[0].message.content
        message_history.append({"role":"assistant", "content":raw_result})
        parsed_result = extract_json(raw_result)

        if not parsed_result:
            print("❌ Model returned invalid JSON. Raw output:\n", raw_result)
            return


        if parsed_result.get("step")=="START":
            print("😶‍🌫️", parsed_result.get("content"))
            continue
        if parsed_result.get("step")=="TOOL":
            tool_to_call = parsed_result.get("tool")
            tool_input = parsed_result.get("input")


            print(f"⚓:{tool_to_call}" )
            tool_response = available_tools[tool_to_call](tool_input)
            message_history.append({"role":"developer", "content":json.dumps(
                {"step":"OBSERVE", "tool":tool_to_call,"input":tool_input , "output":tool_response}
            )})

            
        if parsed_result.get("step")=="PLAN":
            print("😶", parsed_result.get("content"))
            continue
        if parsed_result.get("step")=="OUTPUT":
            print("😍", parsed_result.get("content"))
            continue

        


    


    

main()











