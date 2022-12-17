from tempfile import mkdtemp
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from spotipy.oauth2 import SpotifyOAuth
import spotipy
from helpers import apology, login_required
import secrets

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

users = []

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response
    
# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///project.db")

@app.route("/")
@login_required
def homepage():
    """Show the places to go"""
    return render_template("hi.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")
        
@app.route("/logout")
@login_required
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")
    
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # ensure password (again) was submitted
        elif not request.form.get("confirmation"):
            return apology("must provide password (again)", 400)

        # ensure passwords match
        elif not request.form.get("password") == request.form.get("confirmation"):
            return apology("passwords don't match", 400)

        # Query database for username
        user_check = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # ensure the username is not taken
        if len(user_check) != 0:
            return apology("the username is taken", 400)

        # generate password hash
        password = request.form.get("password")
        hashed_password = str(generate_password_hash(password))

        # register the user
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", request.form.get("username"), hashed_password)

        # Remember which user has logged in
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")
    else:
        return render_template("register.html")
        
@app.route("/movies", methods=["GET", "POST"])
@login_required
def movies():
    if request.method == "GET":
        movies = []
        rows = db.execute("SELECT movie_name FROM movies WHERE user_id=:user_id", user_id=session["user_id"])
        for row in rows:
            movies.append(row["movie_name"])
        return render_template("movies.html", movies=movies)
    else:
        movie_name = request.form.get("movie-input")
        db.execute("INSERT INTO movies(movie_name, user_id) VALUES (:movie_name, :user_id)",
                   movie_name=movie_name,
                   user_id=session["user_id"]
                   )
        flash("New Movie!")
        return redirect("/movies")
    
@app.route("/movie-list", methods=["GET", "POST"])
@login_required
def movie_list():
    if request.method == "GET":
        wished_movies = []
        rows = db.execute("SELECT wished_movie_name FROM wished_movies WHERE user_id=:user_id", user_id=session["user_id"])
        for row in rows:
            wished_movies.append(row["wished_movie_name"])
        return render_template("wished_movies.html", wished_movies=wished_movies)
    else:
        wished_movie_name = request.form.get("wished_movie-input")
        db.execute("INSERT INTO wished_movies(wished_movie_name, user_id) VALUES (:wished_movie_name, :user_id)",
                   wished_movie_name=wished_movie_name,
                   user_id=session["user_id"]
                   )
        flash("New Movie To Watch!")
        return redirect("/movie-list")
    
@app.route("/books", methods=["GET", "POST"])
@login_required
def books():
    if request.method == "GET":
        books = []
        rows = db.execute("SELECT book_name FROM books WHERE user_id=:user_id", user_id=session["user_id"])
        for row in rows:
            books.append(row["book_name"])
        return render_template("books.html", books=books)
    else:
        book_name = request.form.get("book-input")
        db.execute("INSERT INTO books(book_name, user_id) VALUES (:book_name, :user_id)",
                   book_name=book_name,
                   user_id=session["user_id"]
                   )
        flash("New Book!")
        return redirect("/books")
        
    
@app.route("/book-list", methods=["GET", "POST"])
@login_required
def book_list():
    if request.method == "GET":
        wished_books = []
        rows = db.execute("SELECT wished_book_name FROM wished_books WHERE user_id=:user_id", user_id=session["user_id"])
        for row in rows:
            wished_books.append(row["wished_book_name"])
        return render_template("wished_books.html", wished_books=wished_books)
    else:
        wished_book_name = request.form.get("wished_book-input")
        db.execute("INSERT INTO wished_books(wished_book_name, user_id) VALUES (:wished_book_name, :user_id)",
                   wished_book_name=wished_book_name,
                   user_id=session["user_id"]
                   )
        flash("New Book To Read!")
        return redirect("/book-list")

SPOTIFY_CREATE_PLAYLIST_URL= "https://api.spotify.com/v1/users/{}/playlists".format("user_id")
ACCESS_TOKEN = ""
def create_playlist(name, public):
    response = request.post(
        SPOTIFY_CREATE_PLAYLIST_URL,
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}"
        },
        json={
            "name": name,
            # you can add description as a next step
            "public": public
        }
    )
    json_response = response.json()

global sp
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id="e8428daa81a645c79bd69599c62ca09b",
                                                   client_secret="ad668440ec204f93bb23c2a92896c988",
                                                   redirect_uri="http://127.0.0.1:8081/",
                                                   scope="user-library-read playlist-modify-public"))

@app.route("/saved-tracks", methods=["GET"])
@login_required
def saved_tracks():
    music_data = []
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                                   client_secret=CLIENT_SECRET,
                                                   redirect_uri="http://127.0.0.1:8081/",
                                                   scope="user-library-read playlist-modify-public"))
    results = sp.current_user_saved_tracks()
    for idx, item in enumerate(results['items']):
        track = item['track']
        music_data.append(" " + track['artists'][0]['name'] + " – " + track['name'])
    return render_template("playlist-maker.html", music_data=music_data)

@app.route("/music-search", methods=["GET", "POST"])
@login_required
def music_search():
    if request.method == "GET":
        return render_template("music-search.html")
    else:
        music_search_input = request.form.get("music_search_input")
        return redirect(f"/music-search/{music_search_input}")

@app.route("/music-search/<music_search_input>", methods=["GET"])
@login_required
def music_search_input(music_search_input):
    music_search = []
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                                   client_secret=CLIENT_SECRET,
                                                   redirect_uri="http://127.0.0.1:8081/",
                                                   scope="user-library-read playlist-modify-public"))
    results = sp.search(q=music_search_input, limit=20)
    for idx, track in enumerate(results['tracks']['items']):
        music_search.append("" + track['name'])  # adding "" solves type error: tupple indice
    flash("Found!")
    return render_template("music-search.html", music_search=music_search)



if __name__ == '__main__':

    app.run(debug=True, port= 8081)
