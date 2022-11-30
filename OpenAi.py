import os
import openai
from dotenv import load_dotenv 
load_dotenv()

openai.api_key = ""

def ask(question, chat_log=None):
    prompt_text = f'"""You are an AI powered observer. Have a nice chat with the user about anything you like! \n\n""" Q: {question}\n\nA:'
    response = openai.Completion.create(
      engine="text-davinci-002",
      prompt=prompt_text,
      temperature=0.65,
      max_tokens=250,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0,
      stop=["\n"],
    )

    story = response['choices'][0]['text']
    return str(story)

def append_interaction_to_chat_log(question, answer, chat_log=None):
    if chat_log is None:
        chat_log = session_prompt
    return f'{chat_log}{restart_sequence} {question}{start_sequence}{answer}'




