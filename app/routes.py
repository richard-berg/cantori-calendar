from flask import render_template, flash, redirect, url_for, session
from requests import RequestException

from app import app
from app.forms import GetCalendarForm, CustomizeForm
from app.parse import from_webcal


@app.route('/', methods=('GET', 'POST'))
@app.route('/index', methods=('GET', 'POST'))
def index():
    form = GetCalendarForm()
    if form.validate_on_submit():
        session['url'] = form.url.data
        return redirect(url_for('customize'))
    else:
        session['url'] = None
        return render_template('index.html', title='Title Goes Here', form=form)


@app.route('/customize', methods=('GET', 'POST'))
def customize():
    if not session.get('url'):
        flash('Missing URL, starting over...')
        return redirect(url_for('index'))

    form = CustomizeForm()
    try:
        calendar = from_webcal(session['url'])
        form.seasons.choices = [(s, s) for s in calendar.seasons]
        form.groups.choices = [(g, g) for g in calendar.groups]
    except RequestException as e:
        flash('Failed to retrieve calendar:\n' + str(e))
        return redirect(url_for('index'))
    except ValueError as e:
        flash('Failed to parse iCal:\n' + str(e))
        return redirect(url_for('index'))

    if form.validate_on_submit():
        filtered_calendar = (
            calendar
            .filter_seasons(form.seasons.data)
            .filter_groups(form.groups.data)
            .collapse_call_times()
            .shorten_locations()
        )
        return render_template('calendar.html', calendar=filtered_calendar)
    else:
        return render_template('customize.html', form=form)
