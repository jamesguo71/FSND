#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import sys

import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form

from forms import *
from models import db_setup, Venue, Show, Artist

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
db = db_setup(app)

#----------------------------------------------------------------------------#
# Helper Function.
#----------------------------------------------------------------------------#

def now_with_tzinfo(other_time):
    return datetime.now(other_time.tzinfo)

def set_past_and_upcoming_shows(obj):
    def get_show_obj_list(showlist, obj):
        show_obj_list = []
        if isinstance(obj, Venue):
            for show in showlist:
                show_obj_list.append({
                    "artist_id": show.artist_id,
                    "artist_name": show.artist.name,
                    "artist_image_link": show.artist.image_link,
                    "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S.000%Z")
                })
        else:
            for show in showlist:
                show_obj_list.append({
                    "venue_id": show.venue_id,
                    "venue_name": show.venue.name,
                    "venue_image_link": show.venue.image_link,
                    "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S.000%Z")
                })
        return show_obj_list
    past_shows = [show for show in obj.shows if show.start_time < now_with_tzinfo(show.start_time)]
    obj.past_shows = get_show_obj_list(past_shows, obj)
    obj.past_shows_count = len(obj.past_shows)
    upcoming_shows = [show for show in obj.shows if show.start_time >= now_with_tzinfo(show.start_time)]
    obj.upcoming_shows = get_show_obj_list(upcoming_shows, obj)
    obj.upcoming_shows_count = len(obj.upcoming_shows)


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format="EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format="EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues/')
def venues():
    data = []
    unique_state_and_cities = Venue.query.distinct(Venue.city, Venue.state).all()
    for sample_venue in unique_state_and_cities:
        data.append({'city': sample_venue.city,
                     'state': sample_venue.state,
                     'venues': []})
        venues_in_area = Venue.query.filter_by(city=sample_venue.city, state=sample_venue.state).all()
        for venue in venues_in_area:
            num_upcoming_shows = len([show for show in venue.shows if show.start_time >= now_with_tzinfo(show.start_time)])
            venue_data = {'id': venue.id,
                          'name': venue.name,
                          'num_upcoming_shows':num_upcoming_shows}
            data[-1]['venues'].append(venue_data)
    return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
    """
    search on artists with partial string search. Ensure it is case-insensitive.
    """
    data = []
    search_term = request.form.get('search_term')
    match_venues = Venue.query.filter(Venue.name.ilike(f"%{search_term}%")).all()
    for venue in match_venues:
        venue_id = venue.id
        venue_name = venue.name
        num_upcoming_shows = Show.query.filter_by(venue_id=venue_id) \
            .filter(Show.start_time > datetime.now()).count()
        data.append({
            "id": venue_id,
            "name": venue_name,
            "num_upcoming_shows": num_upcoming_shows
        })
    response = {
        "count": len(data),
        "data": data
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    venue = Venue.query.get_or_404(venue_id)
    venue.genres = venue.genres.split(',')
    set_past_and_upcoming_shows(venue)
    return render_template('pages/show_venue.html', venue=venue)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    error = False
    data = {}
    venue_form = VenueForm(request.form)
    if not venue_form.validate():
        return render_template("forms/new_venue.html", form=venue_form)
    try:
        new_venue = Venue()
        venue_form.genres.data = ','.join(venue_form.genres.data)
        venue_form.populate_obj(new_venue)
        db.session.add(new_venue)
        db.session.commit()
        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except Exception as e:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Venue ' + data['name'] + ' could not be listed.')
    return redirect(url_for('index'))

@app.route('/venues/<venue_id>/delete', methods=['GET'])
def delete_venue(venue_id):
    try:
        venue = Venue.query.get_or_404(venue_id)
        db.session.delete(venue)
        db.session.commit()
    except:
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    return redirect(url_for("index"))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists/')
def artists():
    data = []
    for artist in Artist.query.all():
        data.append({
            "id": artist.id,
            "name": artist.name
        })
    return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
    data = []
    search_term = request.form.get('search_term')
    match_artists = Artist.query.filter(Artist.name.ilike(f"%{search_term}%")).all()
    for artist in match_artists:
        artist_id = artist.id
        artist_name = artist.name
        num_upcoming_shows = Show.query.filter_by(artist_id=artist_id)\
            .filter(Show.start_time > datetime.now()).count()
        data.append({
            "id": artist_id,
            "name": artist_name,
            "num_upcoming_shows": num_upcoming_shows
        })
    response = {
        "count": len(data),
        "data": data
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the venue page with the given venue_id
    artist = Artist.query.get_or_404(artist_id)
    artist.genres = artist.genres.split(',')
    set_past_and_upcoming_shows(artist)
    return render_template('pages/show_artist.html', artist=artist)

@app.route('/artists/<int:artist_id>/delete', methods=['GET'])
def delete_artist(artist_id):
    artist = Artist.query.get_or_404(artist_id)
    try:
        db.session.delete(artist)
        db.session.commit()
    except:
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    return redirect(url_for("index"))


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.get_or_404(artist_id)
    form = ArtistForm(obj=artist)
    form.genres.data = artist.genres.split(',')
    return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # artist record with ID <artist_id> using the new attributes
    error = False
    try:
        artist_form = ArtistForm(request.form)
        artist = Artist.query.filter_by(id=artist_id).first_or_404()
        if not artist_form.validate():
            return render_template("forms/edit_artist.html", form=artist_form, artist=artist)
        artist_form.genres.data = ','.join(request.form.getlist('genres'))
        artist_form.populate_obj(artist)
        db.session.commit()
        # on successful db insert, flash success
        flash('Artist ' + request.form['name'] + ' was successfully updated!')
    except Exception as e:
        db.session.rollback()
        error = True
        print(e)
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    venue = Venue.query.get_or_404(venue_id)
    form = VenueForm(obj=venue)
    form.genres.data = venue.genres.split(',')
    return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    form = VenueForm(request.form)
    venue = Venue.query.get_or_404(venue_id)
    if not form.validate():
        return render_template("forms/edit_venue.html", form=form, venue=venue)
    try:
        form.genres.data = ','.join(request.form.getlist('genres'))
        form.populate_obj(venue)
        db.session.commit()
        flash("The venue " + request.form['name'] + "has been successfully updated.")
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash("Something went wrong. The venue " + request.form['name'] + 'has not been updated.')
    finally:
        db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    error = False
    try:
        artist_form = ArtistForm(request.form)
        if not artist_form.validate():
            return render_template("forms/new_artist.html", form=artist_form)
        new_artist = Artist()
        artist_form.genres.data = ','.join(artist_form.genres.data)
        artist_form.populate_obj(new_artist)
        db.session.add(new_artist)
        db.session.commit()
        # on successful db insert, flash success
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    return redirect(url_for('index'))


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    data = []
    for show in Show.query.all():
        venue_id = show.venue_id
        venue_name = Venue.query.get(venue_id).name
        artist_id = show.artist_id
        artist = Artist.query.get(artist_id)
        artist_name = artist.name
        artist_image_link = artist.image_link
        start_time = str(show.start_time)
        data.append({
            "venue_id": venue_id,
            "venue_name": venue_name,
            "artist_id": artist_id,
            "artist_name": artist_name,
            "artist_image_link": artist_image_link,
            "start_time": start_time
        })
    return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    error = False
    try:
        show_form = ShowForm(request.form)
        if not show_form.validate():
            return render_template('forms/new_show.html', form=show_form)
        f = request.form
        venue_id = f.get('venue_id')
        artist_id = f.get('artist_id')
        if Venue.query.get(venue_id) and Artist.query.get(artist_id):
            new_show = Show(venue_id=venue_id, artist_id=artist_id, start_time=f.get('start_time'))
            db.session.add(new_show)
            db.session.commit()
            flash('Show was successfully listed!')
        else:
            raise ValueError("No such venue id or artist id.")
    except ValueError as e:
        error = True
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred. %s Show could not be listed.' % e)
    finally:
        db.session.close()
    # on successful db insert, flash success
    return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
