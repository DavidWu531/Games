from app.routes import db

# Many-to-many Relationship Table
PizzaTopping = db.Table('PizzaTopping',
    db.Column('PizzaID', db.Integer, db.ForeignKey('Pizza.PizzaID')),  # noqa E128
    db.Column('ToppingID', db.Integer, db.ForeignKey('Topping.ToppingID'))
)  # noqa: E501


class Game(db.Model):
    __tablename__ = 'Games'

    GameID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    GameName = db.Column(db.String(255), nullable=False)
    GameDescription = db.Column(db.Text)
    GameReleaseDate = db.Column(db.Date)
    GamePrice = db.Column(db.Float)
    GameImage = db.Column(db.String(255))

    categories = db.relationship('Category', secondary='GameCategories', back_populates='games')
    platforms = db.relationship('Platform', secondary='GamePlatforms', back_populates='games')
    system_requirements = db.relationship('SystemRequirement', back_populates='game', cascade="all, delete-orphan")


class Category(db.Model):
    __tablename__ = 'Categories'

    CategoryID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    CategoryName = db.Column(db.String(100), nullable=False)
    CategoryDescription = db.Column(db.Text)

    games = db.relationship('Game', secondary='GameCategories', back_populates='categories')


class GameCategory(db.Model):
    __tablename__ = 'GameCategories'

    GameID = db.Column(db.Integer, db.ForeignKey('Games.GameID', ondelete='CASCADE'), primary_key=True)
    CategoryID = db.Column(db.Integer, db.ForeignKey('Categories.CategoryID', ondelete='CASCADE'), primary_key=True)


class Platform(db.Model):
    __tablename__ = 'Platforms'

    PlatformID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    PlatformName = db.Column(db.String(100), nullable=False)
    PlatformDescription = db.Column(db.Text)

    games = db.relationship('Game', secondary='GamePlatforms', back_populates='platforms')


class GamePlatform(db.Model):
    __tablename__ = 'GamePlatforms'

    GameID = db.Column(db.Integer, db.ForeignKey('Games.GameID', ondelete='CASCADE'), primary_key=True)
    PlatformID = db.Column(db.Integer, db.ForeignKey('Platforms.PlatformID', ondelete='CASCADE'), primary_key=True)


class SystemRequirement(db.Model):
    __tablename__ = 'SystemRequirements'

    RequirementsID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    GameID = db.Column(db.Integer, db.ForeignKey('Games.GameID', ondelete='CASCADE'), nullable=False)
    Type = db.Column(db.String(12), nullable=False)  # 'Minimum' or 'Recommended'
    OS = db.Column(db.String(100))
    RAM = db.Column(db.String(50))
    CPU = db.Column(db.String(100))
    GPU = db.Column(db.String(100))
    Storage = db.Column(db.String(50))

    game = db.relationship('Game', back_populates='system_requirements')


# class Pizza(db.Model):
#     __tablename__ = "Pizza"
#     id = db.Column(db.Integer, primary_key = True)  # noqa
#     name = db.Column(db.String())
#     description = db.Column(db.Text())
#     base = db.Column(db.Integer, db.ForeignKey('Base.BaseID'))

#     base_name = db.relationship("Base", backref = "pizzas_with_this_base")  # noqa

#     def __repr__(self):
#         return f'{self.name.upper()} PIZZA'
