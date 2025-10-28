from flask import Flask

from blueprints.movies.movies import moviesBP
from blueprints.reviews.reviews import reviewsBP
from blueprints.auth.auth import authBP
from blueprints.platforms.platforms import platformsBP

app = Flask(__name__)

app.register_blueprint(moviesBP)
app.register_blueprint(reviewsBP)
app.register_blueprint(authBP)
app.register_blueprint(platformsBP)


if __name__ == "__main__":
    app.run(debug=True)