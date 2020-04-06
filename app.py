# Import error? https://stackoverflow.com/questions/48161530/i-cannot-use-pylint-in-vsc-using-pipenv-bash-for-windows-10
# Point your python.pythonPath to the current virtual env
# See what the current vitual env is by running pipenv shell
from locale import atof
import pandas as pd
from pandas.io.json import json_normalize
from flask_bootstrap import Bootstrap
from flask import Flask, render_template, request, jsonify
import matplotlib.pyplot as plt
import requests
import locale
import matplotlib
import os
from bokeh.plotting import figure, show
from bokeh.io import output_notebook
from bokeh.models import CategoricalColorMapper, ColumnDataSource
from bokeh.embed import json_item
import json
from flask_cors import CORS


# Set configs
locale.setlocale(locale.LC_NUMERIC, '')
matplotlib.pyplot.switch_backend('Agg')

app = Flask(__name__)
CORS(app)
bootstrap = Bootstrap(app)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# Main Routes
@app.route('/')
def index():
    corona_data = requests.get('https://corona.lmao.ninja/all').json()
    return render_template('corona.html', data=corona_data)


@app.route('/countries')
def countries():
    corona_countries_data = requests.get(
        'https://corona.lmao.ninja/countries').json()
    df = json_normalize(corona_countries_data)
    return render_template('countries.html', data=df.to_html())


@app.route('/top_10')
def top_ten():
    url = "https://coronavirus-monitor.p.rapidapi.com/coronavirus/cases_by_country.php"
    headers = {'x-rapidapi-host': "coronavirus-monitor.p.rapidapi.com",
               'x-rapidapi-key': "354bbfff0dmsh2143a138716e8fcp130991jsn814a6b3be289"}
    r = requests.get(url, headers=headers)
    # Clean the data
    df_cases_by_country = json_normalize(r.json()['countries_stat'])
    df_cases_by_country.set_index('country_name', drop=True, inplace=True)
    columns_of_interest = ['cases', 'deaths', 'total_recovered', 'new_deaths',
                           'new_cases', 'serious_critical', 'active_cases', 'total_cases_per_1m_population']
    df_cases_by_country = df_cases_by_country[columns_of_interest].applymap(
        atof)
    # Def a function to render the plots

    def make_plots(columnName):
        # Make the figures
        fig, ax = plt.subplots()
        # Deaths
        top_ten_deaths = df_cases_by_country[[columnName]].iloc[0:9, :].sort_values(
            ascending=False, by=[columnName])
        ax.bar(top_ten_deaths.index, top_ten_deaths[columnName])
        ax.set_xticklabels(top_ten_deaths.index, rotation=90)
        ax.set_ylabel('Number of ' + columnName)
        #  Save the fig
        script_dir = os.path.dirname(__file__)
        results_dir = os.path.join(script_dir, 'static/top_10/')
        sample_file_name = columnName+".png"
        fig.savefig(results_dir + sample_file_name)

    # make the plots
    for columnName in columns_of_interest[0:3]:
        make_plots(columnName)
    # Render the remplate
    return render_template('top_10.html')

# VEOCI API

def getCategoricalColorMapperObj(colorMapperData):
    if (colorMapperData):
        factors = colorMapperData['factors']
        palette = colorMapperData['palette']
        transform = CategoricalColorMapper(factors=factors, palette=palette)
        field = colorMapperData['field']['index']
        return dict(field=field, transform=transform)
    return None

@app.route('/renderplot', methods=['POST'])
def renderplot():
    try:
        data = request.get_json()
        entries = list(map(lambda x: x['values'], data['entriesData']))
        plot_meta = data['plotData']
        uuid = data['uuid']
        # Convert data to a DF
        df = pd.DataFrame(entries)
        column_count = len(df.count())
        column_names = [str(index) for index in range(column_count)]
        df.columns = column_names

        # Get the template data
        plot_data = json.loads(plot_meta['state'])
        template_info = plot_data['template']
        xAxisField = template_info['xAxisField'] or ''
        xAxisFieldIndex = xAxisField['index']
        xAxisFieldVeociType = xAxisField['fieldType']
        if (xAxisFieldVeociType == 'NUMERIC'):
            df[xAxisFieldIndex] = df[xAxisFieldIndex].apply(pd.to_numeric)

        yAxisField = template_info['yAxisField'] or ''
        yAxisFieldIndex = yAxisField['index']
        yAxisFieldVeociType = yAxisField['fieldType']
        if (yAxisFieldVeociType == 'NUMERIC'):
            df[yAxisFieldIndex] = df[yAxisFieldIndex].apply(pd.to_numeric)

        # Get the figure info wired
        title = template_info['title'] or ''
        x_axis_label = template_info['xAxisLabel'] or ''
        y_axis_label = template_info['yAxisLabel'] or ''

        figure_meta = {
            'title': title,
            'x_axis_label': x_axis_label,
            'y_axis_label': y_axis_label
        }
        p = figure(**figure_meta)

        # Convert df to a ColumnDataSource: source
        source = ColumnDataSource(df)

        # Get styling stuff
        colorMapper = template_info['colorMapper'] or None
        color_mapper = getCategoricalColorMapperObj(colorMapper)

        glyph_meta = {
            'x': xAxisField['index'],
            'y': yAxisField['index'],
            'color': color_mapper,
            'source': source
        }

        # Add a circle glyph to the figure p
        p.circle(**glyph_meta)

        # Send back json
        plot_json = json.dumps(json_item(p, uuid))
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True,
            },
            'body': plot_json
        }
    except Exception as exc:
        print(exc)
        return {
            'statusCode': 400,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': True
            },
            'body': '{"status": "failiure occured!"}',
        }


if __name__ == "__main__":
    app.run()
