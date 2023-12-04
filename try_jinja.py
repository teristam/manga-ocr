#%%
import jinja2
from jinja2 import FileSystemLoader, Environment

env  = Environment(loader=FileSystemLoader('templates/'))

template = env.get_template('message.txt')

display(template.render(name='World', score=19))

#%%
template = 