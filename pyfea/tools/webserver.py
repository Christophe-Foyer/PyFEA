import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from plotly import graph_objs as go

def drawtet(points, value):
    go.Mesh3d(
        x=[0, 1, 2, 0],
        y=[0, 0, 1, 2],
        z=[0, 2, 0, 1],
        colorbar_title='z',
        colorscale=[[0, 'gold'], 
                    [0.5, 'mediumturquoise'], 
                    [1, 'magenta']],
        # Intensity of each vertex, which will be interpolated and color-coded
        intensity=[0, 0.33, 0.66, 1],
        # i, j and k give the vertices of triangles
        # here we represent the 4 triangles of the tetrahedron surface
        i=[0, 0, 0, 1],
        j=[1, 2, 3, 2],
        k=[2, 3, 1, 3],
        name='y',
        showscale=True
    )

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    dcc.Input(id='my-id', value='initial value', type='text'),
    html.Div(id='my-div')
])


@app.callback(
    Output(component_id='my-div', component_property='children'),
    [Input(component_id='my-id', component_property='value')]
)
def update_output_div(input_value):
    return 'You\'ve entered "{}"'.format(input_value)


if __name__ == '__main__':
    app.run_server(debug=True)
    
else:
    # If not start is as main in its own process!
    
    import subprocess
    import atexit
    import psutil
    
    print("Starting webserver")
    print(__file__)
    
    process = subprocess.Popen(["python", __file__], shell=True)
    
    def kill(proc_pid):
        p = psutil.Process(proc_pid)
        for proc in p.children(recursive=True):
            proc.kill()
        p.kill()
    
    def cleanup():
        print("Cleaning up webserver...")
        kill(process.pid)
    
    atexit.register(cleanup)