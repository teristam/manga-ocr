#%% 
import pandas as pd
import difflib
import numpy as np
from manga_ocr import MangaOcr
from PIL import ImageGrab, Image
import pyperclip
from loguru import logger
from manga_ocr.run import are_images_identical
import time 
import gradio as gr
import jinja2
import re
from jinja2 import FileSystemLoader, Environment
env  = Environment(loader=FileSystemLoader('templates/'))

# %%
story = pd.read_excel('game_scripts/Final Fantasy 06.xlsx', names=[
    'index', 'cha_jp', 'cha_eng', 'jp', 'eng'], sheet_name='Story')
story = story.fillna('')
# %%

def find_match(s, ref, col2match='jp'):
    matched_lines = difflib.get_close_matches(s, ref[col2match], cutoff=0.5)
    rows = [ref[ref[col2match]==ln] for ln in matched_lines]
    if len(rows)>0:
        return pd.concat(rows,axis=0)
    else:
        return None

def process_results(mocr, img_or_path):
    t0 = time.time()
    text = mocr(img_or_path)
    t1 = time.time()

    logger.info(f'Text recognized in {t1 - t0:0.03f} s: {text}')

    return text

# %%
# def parse_text_output(t):
#     # convert the dataframe from script matching to text
#     s = ''
#     for _,row in t.iterrows():
#         s+=row['jp'].replace('\\n', '<br/>')
#         s+='<br/><br/>'
#         s+=row['eng'].replace('\\n', '<br/>')
#         s+='<hr/>'
#     return s

def clean_up(s):
    s = re.sub('<.*?>', '', s)
    s = re.sub(r'\n','<br/>', s)
    return s

def parse_text_output(r):
    template = env.get_template('text_table.txt')
    # clean up the dataframe
    r.loc[:,'jp'] = r['jp'].apply(clean_up)
    r.loc[:,'eng'] = r['eng'].apply(clean_up)

    return template.render(dataframe=r)
    
# parse_text_output(r)


#%%
pretrained_model_name_or_path='kha-white/manga-ocr-base'
mocr = MangaOcr(pretrained_model_name_or_path, force_cpu=False)

verbose = True
def process_clipboard(state):
    # print('processing')
    last_text = state['last_text']
    try:
        img = ImageGrab.grabclipboard()
        # print(img)
    except OSError as error:
        if not verbose and "cannot identify image file" in str(error):
            # Pillow error when clipboard hasn't changed since last grab (Linux)
            pass
        elif not verbose and "target image/png not available" in str(error):
            # Pillow error when clipboard contains text (Linux, X11)
            pass
        else:
            logger.warning('Error while reading from clipboard ({})'.format(error))
    else:
        if isinstance(img, Image.Image):
            # print('Now analyzing')
            if not are_images_identical(img, state['last_img']):
                text = process_results(mocr, img)
                matched_line = find_match(text, story)
                if matched_line is not None:
                    pyperclip.copy(matched_line.iloc[0].jp)
                    text = parse_text_output(matched_line[['jp','eng']])
                    state['last_img'] = img 
                    state['last_text']  = text
                    return state, text
                else:
                    return state, text
            else:
                return state, last_text
        else:
            return state, last_text

with gr.Blocks() as demo:
    state = gr.State({'last_img':None, 'last_text': None})
    btn = gr.Button('Start')
    output = gr.HTML()

    btn.click(
        process_clipboard,
        [state],
        [state, output],
        every=0.5
    )
    
if __name__ == '__main__':
    demo.launch()
    
    
'''
TODO:
1. automatically identify textbox to extract
2. clean up text
3. include text to voice function
'''