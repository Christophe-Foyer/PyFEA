import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from plotly import graph_objs as go
import sys
import numpy as np
import pickle

import requests
import threading

import pandas as pd

pyfea_data={}

def drawtets(nodes, tets, values):
    
    try:
        nodes = np.array(nodes)
        tets = np.array(tets)
        values = np.array(values)
        
    #    assert tets.shape[1] == 4
        
        #tets helper
        t_h = np.hstack([tets,tets[:,:2]])
        tri = np.vstack([t_h[:,0:3],t_h[:,1:4],t_h[:,2:5],t_h[:,3:6]])
        tri = np.rot90(tri,-1)
        
        return go.Mesh3d(
            x=nodes[:,0].flatten(), #x=[0, 1, 2, 0],
            y=nodes[:,1].flatten(), #y=[0, 0, 1, 2],
            z=nodes[:,2].flatten(), #z=[0, 2, 0, 1],
    #        colorbar_title='values',
            colorscale=[[0, 'gold'], 
                        [0.5, 'mediumturquoise'], 
                        [1, 'magenta']],
            # Intensity of each vertex, which will be interpolated and color-coded
            intensity=np.rot90(np.vstack([values]*4),-1).flatten(), #intensity=[0, 0.33, 0.66, 1],
            # i, j and k give the vertices of triangles
            # here we represent the 4 triangles of the tetrahedron surface
            i=tri[0].flatten(),    #i=[0, 0, 0, 1],
            j=tri[1].flatten(),    #j=[1, 2, 3, 2],
            k=tri[2].flatten(),    #k=[2, 3, 1, 3],
            name='tets',
            showscale=True
        )
    except:
        return go.Mesh3d()

#go.Figure(data=[drawtets(sim.assembly.nodes, sim.assembly.tets, sim.variables.T)]).show()

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# %%Layout

def getdata(key=None):
    try:
        #TODO: switch to restful
        file = pyfea_data['tempfile']
            
        with open(file) as f:  # Python 3: open(..., 'rb')
            if key:
                return pickle.load(f)[key]
            else:
                return pickle.load(f)
            
    except:
        class obj:
            def __enter__(self):
                return None
            def __getattribute__(self, name):
                return None
        return obj()
    
app.layout = \
html.Div([
#    dcc.Input(id='my-id', value='initial value', type='text'),
#    html.Div(id='my-div'),
#    
#    html.Div(id='live-update-text'),
    
#    dcc.Graph(
#        id='3D-graph',
#        figure=go.Figure(data=[drawtets(getdata('nodes'),
#                                        getdata('tets'),
#                                        getdata('variables').T)])
#        ),
            
    dcc.Interval(
            id='interval-component',
            interval=5*1000, # in milliseconds
            n_intervals=0
        )
])

# %% Callbacks

@app.callback(
    Output(component_id='live-update-text', component_property='children'),
    [Input(component_id='interval-component', component_property='n_intervals')]
)
def update_temp(n):
    #This needs to be moved to its own loop
    r = requests.get(pyfea_data['restful']+'/sim_data')
    mean = pd.DataFrame(r.json()['data'])['T'].mean()
    print('Wat', mean)
    return 'Temp value: "{}"'.format(mean)

#@app.callback(
#    Output(component_id='my-div', component_property='children'),
#    [Input(component_id='my-id', component_property='value')]
#)
#def update_output_div(input_value):
#    return 'You\'ve entered "{}"'.format(input_value)

# %% Setup



if len(sys.argv) > 1:
    pyfea_data={'restful': sys.argv[1]}
else:
    port = input('RESTful api port: ')
    pyfea_data={'restful':'http://localhost:' + str(port)}
    
#Keepalive thread: If restful dies we do too 
#(maybe this whole program should just be threaded...)
def keepalive():
    import time
    while True:
        ret = requests.get(pyfea_data['restful'])
        if type(ret) != requests.models.Response:
            exit()
        time.sleep(1)
threading.Thread(target=keepalive)

app.run_server(debug=False)