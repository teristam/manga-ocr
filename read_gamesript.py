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
# %%
story = pd.read_excel('game_scripts/Final Fantasy 06.xlsx', names=[
    'index', 'cha_jp', 'cha_eng', 'jp', 'eng'], sheet_name='Story')
story = story.fillna('')
# %%

def find_match(s, ref, col2match='jp'):
    matched_lines = difflib.get_close_matches(s, ref[col2match], cutoff=0.5)
    rows = [ref[ref[col2match]==ln] for ln in matched_lines]
    if len(rows)>0:
        return pd.concat(rows)
    else:
        return None

def process_results(mocr, img_or_path):
    t0 = time.time()
    text = mocr(img_or_path)
    t1 = time.time()

    logger.info(f'Text recognized in {t1 - t0:0.03f} s: {text}')

    
    matched_rows = find_match(text, story)
    return matched_rows

# %%
pretrained_model_name_or_path='kha-white/manga-ocr-base'
mocr = MangaOcr(pretrained_model_name_or_path, force_cpu=False)

def parse_text_output(text):
    # convert the dataframe from script matching to text
    s = ''
    
    for _,row in text:
        s+=row['jp']
        s+='\n\n'
        s+=row['eng']
        s+='----------\n\n'
    return s


def process_clipboard(state):
    # print('processing')
    last_text = state['last_text']
    try:
        img = ImageGrab.grabclipboard()
        print(img)
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
                state['last_img'] = img 
                state['last_text']  = parse_text_output(text)
                return state, text
            else:
                return state, last_text
        else:
            return state, last_text

with gr.Blocks() as demo:
    state = gr.State({'last_img':None, 'last_text': None})
    output = gr.TextArea(lines=10, container=True, min_width = 100, interactive=False)
    btn = gr.Button('Start')
    btn.click(
        process_clipboard,
        [state],
        [state, output],
        every=0.5
    )
    
if __name__ == '__main__':
    demo.launch()