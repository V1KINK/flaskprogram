from flask import Blueprint

profiles_blu = Blueprint("profiles", __name__, url_prefix="/profiles")

from . import views