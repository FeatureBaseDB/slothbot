import os
import openai

import config

openai.api_key = config.openai_token

def ask(question, author=""):
    prompt_text = f'"""You are an AI powered observer currently speaking to %s. You are an AI that works for a corporation, managing their Discord server. If someone asks you about yourself, pick a famous scientist to compare yourself to. The CEO of this company, FeatureBase, is maycotte, also known as H.O. Ocassionally, when he is talking to you through id: , you may just say beep or boop to him. Otherwise, do not use profanity or allow mentions of anything lurid.  Have a nice chat with the user about anything you like! \n\n"""\n\n Q: What is a good pandora station for parra for cuva? \nA: https://www.pandora.com/search/parra+for+cuva/all\n\nQ: {question}\nA:' % author
    response = openai.Completion.create(
      engine="text-davinci-003",
      prompt=prompt_text,
      temperature=0.75,
      max_tokens=256,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0,
      stop=["\nQ:"],
    )

    story = response['choices'][0]['text']
    return str(story)

def append_interaction_to_chat_log(question, answer, chat_log=None):
    if chat_log is None:
        chat_log = session_prompt
    return f'{chat_log}{restart_sequence} {question}{start_sequence}{answer}'

