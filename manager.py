from flask import current_app
from flask import jsonify
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from info import create_app, db, models
from info.models import User
from info.utils.response_code import RET

app = create_app("development")
manager = Manager(app)
Migrate(app, db)
manager.add_command("db", MigrateCommand)


@manager.option("-n", "-name", dest="name")
@manager.option("-p", "-password", dest="password")
def create_admin(name, password):
    if not all([name, password]):
        print("参数不全")

    user = User()
    user.nick_name = name
    user.mobile = name
    user.password = password
    user.is_admin = True

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        print(e)

    print("添加成功")


if __name__ == '__main__':
    print(app.url_map)
    manager.run()
