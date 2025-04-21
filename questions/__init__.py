from flask import Blueprint

questions_bp = Blueprint('questions', __name__)

from questions import routes