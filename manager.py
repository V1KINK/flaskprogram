from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from info import create_app, db


manager = Manager(create_app)
Migrate(create_app, db)
manager.add_command("db", MigrateCommand)
app = create_app("development")


@app.route("/")
def index():
    return "index"


if __name__ == '__main__':
    manager.run()
