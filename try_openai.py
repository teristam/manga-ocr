#%%
from openai import OpenAI
import json
import time 

def show_json(obj):
    display(json.loads(obj.model_dump_json()))
    
    
def wait_on_run(run,thread):
    while run.status == 'queued' or run.status == 'in_progress':
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id = run.id
        )
        time.sleep(0.5)
        
    return run

#%%
client = OpenAI()

# %%
sensei = client.beta.assistants.retrieve('asst_xJhqcT3I1g6lLiJtQtLJFbiA')

def submit_message(assistant_id, thread, user_message):
    # create a message
    message = client.beta.threads.messages.create(
        thread_id = thread.id,
        role='user',
        content = user_message
    )
    
    # execute run
    run = client.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id= sensei.id,
    )
    
    return run
    

def create_thread_and_run(user_message):
    # create a thread
    thread = client.beta.threads.create()
    run = submit_message(sensei, thread, user_message)
    return thread, run

def get_response(thread, run):
    messages = wait_on_run(run, thread) #wait till the run is complete
    messages = client.beta.threads.messages.list(
        thread_id=thread.id
    )
    return list(messages)[0].content[0].text.value #extract the response

thread, run = create_thread_and_run('/grammar いや、手応えがなかった')
response = get_response(thread, run)
response


# %% Chat-completion API

system_prompt = '''
Your role is to be a Japanese language tutor, specializing in advanced topics suitable for learners at the N2 level. Focus on explaining complex grammar points, nuances in language use, and providing in-depth example sentences. Ensure your explanations are culturally accurate and detailed, helping learners grasp subtleties and improve their proficiency. Tailor your responses to challenge and engage learners who already have a solid foundation in Japanese.
Always use furigana, never use romanji for the reading. Explain in English.

When provided with the following commands, carry out the request action:
/grammar explain the grammar points of the sentence, adding extra examples if possible
/proofread check the grammar of the provided sentence, indicating whether there is any grammatical mistake or strange expression
'''
#%%
completion = client.chat.completions.create(
    model='gpt-4-1106-preview',
    messages = [
        {'role':'system', 'content': system_prompt},
        {'role': 'user', 'content':'/grammar いや、手応えがなかった'}
    ],
    stream=True)

#response['choices'][0]['message']['content']
for chunk in completion:
    print(chunk)
    print(chunk.choices[0].delta.content)
    print('--------')
# %%
