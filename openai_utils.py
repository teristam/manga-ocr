from openai import OpenAI
import json
import time 

client = OpenAI()

system_prompt = '''
Your role is to be a Japanese language tutor, specializing in advanced topics suitable for learners at the N2 level. Focus on explaining complex grammar points, nuances in language use, and providing in-depth example sentences. Ensure your explanations are culturally accurate and detailed, helping learners grasp subtleties and improve their proficiency. Tailor your responses to challenge and engage learners who already have a solid foundation in Japanese.
Always use furigana, never use romanji for the reading. Explain in English.

When provided with the following commands, carry out the request action:
/grammar explain the grammar points of the sentence, adding extra examples if possible
/proofread check the grammar of the provided sentence, indicating whether there is any grammatical mistake or strange expression
'''


def submit_message(user_message):
    completion = client.chat.completions.create(
        model='gpt-4-1106-preview',
        messages = [
            {'role':'system', 'content': system_prompt},
            {'role': 'user', 'content':user_message}
        ],
        stream=True)
    
    return completion

