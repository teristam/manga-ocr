from nicegui import ui, app
import utils
from PIL import ImageGrab, Image
import pandas as pd 
import pyperclip
from loguru import logger
from manga_ocr import MangaOcr
from collections import deque
from jinja2 import FileSystemLoader, Environment

#%%

env  = Environment(loader=FileSystemLoader('templates/'))
pretrained_model_name_or_path='kha-white/manga-ocr-base'
mocr = MangaOcr(pretrained_model_name_or_path, force_cpu=False)
data = {
    'last_img': None,
    'filepath': '',
    'story': None,
    'start_scan': False,
    'history': deque(maxlen=10)
}

test_data = pd.DataFrame({
    'jp': ['今は、この都市のガードに追われている', '今は、この都市のガードに追われている'],
    'eng': ['testing testing', 'testing...testing']
})

test_data2 = pd.DataFrame({
    'jp': ['いや、手応えがなかった…… 水中に潜っただけかも……？！'],
    'eng': ['testing testing']
})

data['history'].appendleft(test_data)
data['history'].appendleft(test_data2)


def open_file_handler():
    data['filepath'] = utils.get_any_file_path()
    

def process_clipboard():
    if not data['start_scan']:
        return 
    
    # logger.info('Scanning')
    game_script_path = data['filepath']
    last_img = data['last_img']
    story = data['story']
    
    #load game script on first run
    if story is None:
        story = utils.load_gamescript(game_script_path)        
        data['story'] = story
        assert story is not None
    
    try:
        img = ImageGrab.grabclipboard()
        # print(img)
    except OSError as error:
        if "cannot identify image file" in str(error):
            # Pillow error when clipboard hasn't changed since last grab (Linux)
            pass
        elif "target image/png not available" in str(error):
            # Pillow error when clipboard contains text (Linux, X11)
            pass
        else:
            logger.warning('Error while reading from clipboard ({})'.format(error))
    else:
        if isinstance(img, Image.Image):
            '''
            if found a match in game script file, return the corresponding rows in the gamescript
            If no match is found, return the OCR text
            only do recognization if the image is different to save processing power
            '''
            if not utils.are_images_identical(img, last_img):
                print('Processing new image')
                text = utils.process_results(mocr, img)
                matched_line = utils.find_match(text, story)
                logger.info(matched_line)
                if matched_line is not None:
                    jptext = matched_line.iloc[0].jp
                    df_results = matched_line[['jp','eng']]
                    df_results = utils.clean_up_df(df_results)
                else:
                    jptext = text
                    df_results = pd.DataFrame([{'jp':text, 'eng':''}])
                    
                pyperclip.copy(jptext)
                data['last_img'] = img 
                data['last_text']  = text
                
                data['history'].appendleft(df_results)
            else:
                print('Same images. skipping')
            
            
            html = utils.parse_text_output(data['history'], env)

            print_results.refresh() # need to call the refresh function directly

        

@ui.refreshable
def print_results():
    # logger.info(len(data['history']))
    for res in data['history']:
        with ui.card() as card:
            card.tailwind.margin('my-2').width('full')
            for _, row in res.iterrows():
                ui.label(row['jp']).tailwind.font_size('lg')
                ui.label(row['eng']).tailwind.text_color('gray-500')
        

def start_scan():
    data['start_scan'] = True


@ui.page('/')
def index():
    with ui.row() as container:
        container.tailwind.width('full')
        #app.storage.user requires a session ID, so must be within a page builder
        path_input =ui.input('').bind_value(data, 'filepath')
        ui.button('Load', on_click = open_file_handler)
        ui.button('Start', on_click = start_scan)
    scan_timer = ui.timer(1, process_clipboard, active=True)
    print_results() #have to be at least called once

        
ui.run(storage_secret='abcd', dark=True)