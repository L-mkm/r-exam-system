from flask import Blueprint

exams_bp = Blueprint('exams', __name__, url_prefix='/exams')

from . import routes
from . import student_routes