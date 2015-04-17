from flask import Blueprint

mod = Blueprint(
    'bower',
    __name__,
    static_folder='../static'
)
