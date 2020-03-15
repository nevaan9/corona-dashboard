# Import error? https://stackoverflow.com/questions/48161530/i-cannot-use-pylint-in-vsc-using-pipenv-bash-for-windows-10
# Point your python.pythonPath to the current virtual env
# See what the current vitual env is by running pipenv shell
from flask import Flask, render_template
from flask_bootstrap import Bootstrap
import requests
from pandas.io.json import json_normalize

app = Flask(__name__)
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


if __name__ == "__main__":
    app.run()
