from app.routes import db

# Many-to-many Relationship Table
# PizzaTopping = db.Table("PizzaTopping",
#     db.Column("PizzaID", db.Integer, db.ForeignKey("Pizza.PizzaID")),
#     db.Column("ToppingID", db.Integer, db.ForeignKey("Topping.ToppingID"))
# )


GameCategories = db.Table("GameCategories",
                          db.Column("GameID", db.Integer, db.ForeignKey("Games.GameID", ondelete="CASCADE")),
                          db.Column("CategoryID", db.Integer, db.ForeignKey("Categories.CategoryID", ondelete="CASCADE"))
                          )

GamePlatforms = db.Table("GamePlatforms",
                         db.Column("GameID", db.Integer, db.ForeignKey("Games.GameID", ondelete="CASCADE")),
                         db.Column("PlatformID", db.Integer, db.ForeignKey("Platforms.PlatformID", ondelete="CASCADE"))
                         )


class Games(db.Model):
    __tablename__ = "Games"

    GameID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    GameName = db.Column(db.String(255), nullable=False)
    GameDescription = db.Column(db.String(255))
    GameDeveloper = db.Column(db.String(255))
    GameImage = db.Column(db.String(255))

    categories = db.relationship("Categories", secondary="GameCategories", back_populates="games")
    platforms = db.relationship("Platforms", secondary="GamePlatforms", back_populates="games")
    system_requirements = db.relationship("SystemRequirements", back_populates="games", cascade="all, delete-orphan")
    game_platform_details = db.relationship("GamePlatformDetails", back_populates="games", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Game {self.GameName}>"


class Categories(db.Model):
    __tablename__ = "Categories"

    CategoryID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    CategoryName = db.Column(db.String(100), nullable=False)
    CategoryDescription = db.Column(db.Text)

    games = db.relationship("Games", secondary="GameCategories", back_populates="categories")

    def __repr__(self):
        return f"<Category {self.CategoryName}>"


class Platforms(db.Model):
    __tablename__ = "Platforms"

    PlatformID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    PlatformName = db.Column(db.String(100), nullable=False)
    PlatformDescription = db.Column(db.String(255))

    games = db.relationship("Games", secondary="GamePlatforms", back_populates="platforms")
    game_platform_details = db.relationship("GamePlatformDetails", back_populates="platforms", cascade="all, delete-orphan")
    system_requirements = db.relationship("SystemRequirements", back_populates="platforms", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Platform {self.PlatformName}>"


class SystemRequirements(db.Model):
    __tablename__ = "SystemRequirements"

    RequirementsID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    GameID = db.Column(db.Integer, db.ForeignKey("Games.GameID", ondelete="CASCADE"), nullable=False)
    PlatformID = db.Column(db.Integer, db.ForeignKey("Platforms.PlatformID", ondelete="CASCADE"), nullable=False)
    Type = db.Column(db.String(12), nullable=False)  # "Minimum" or "Recommended"
    OS = db.Column(db.String(100))
    RAM = db.Column(db.String(50))
    CPU = db.Column(db.String(100))
    GPU = db.Column(db.String(100))
    Storage = db.Column(db.String(50))

    games = db.relationship("Games", back_populates="system_requirements")
    platforms = db.relationship("Platforms", back_populates="system_requirements")

    def __repr__(self):
        return f"<SystemRequirement {self.Type} for Game {self.GameID}>"


class GamePlatformDetails(db.Model):
    __tablename__ = "GamePlatformDetails"
    __table_args__ = (
        db.PrimaryKeyConstraint("GameID", "PlatformID"),
    )

    GameID = db.Column(db.Integer, db.ForeignKey("Games.GameID", ondelete="CASCADE"), nullable=False, primary_key=True)
    PlatformID = db.Column(db.Integer, db.ForeignKey("Platforms.PlatformID", ondelete="CASCADE"), nullable=False, primary_key=True)
    Price = db.Column(db.Float)
    ReleaseDate = db.Column(db.String(10))

    games = db.relationship("Games", back_populates="game_platform_details")
    platforms = db.relationship("Platforms", back_populates="game_platform_details")

    def __repr__(self):
        return f">GamePlatformDetails {self.GameID} for Platform {self.PlatformID}"


class Reviews(db.Model):
    __tablename__ = "Reviews"
    __tableargs__ = (
        db.CheckConstraint("Rating BETWEEN 1 AND 5", name="check_rating_between_1_and_5")
    )

    ReviewID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    UserID = db.Column(db.Integer, db.ForeignKey("Accounts.AccountID", ondelete="CASCADE"), nullable=False)
    GameID = db.Column(db.Integer, db.ForeignKey("Games.GameID", ondelete="CASCADE"), nullable=False)
    Rating = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<Reviews {self.GameID} {self.ReviewID} for {self.GameID}"


class Accounts(db.Model):
    __tablename__ = "Accounts"

    AccountID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    AccountUsername = db.Column(db.Text, nullable=False, unique=True)
    AccountPassword = db.Column(db.Text, nullable=False)

    def __init__(self, AccountUsername, AccountPassword):
        self.AccountUsername = AccountUsername
        self.AccountPassword = AccountPassword


# class Pizza(db.Model):
#     __tablename__ = "Pizza"
#     id = db.Column(db.Integer, primary_key = True)
#     name = db.Column(db.String())
#     description = db.Column(db.Text())
#     base = db.Column(db.Integer, db.ForeignKey("Base.BaseID"))

#     base_name = db.relationship("Base", backref = "pizzas_with_this_base")

#     def __repr__(self):
#         return f"{self.name.upper()} PIZZA"
