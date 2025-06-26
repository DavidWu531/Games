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

    def __repr__(self):
        return f"<Platform {self.PlatformName}>"


class SystemRequirements(db.Model):
    __tablename__ = "SystemRequirements"

    RequirementsID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    GameID = db.Column(db.Integer, db.ForeignKey("Games.GameID", ondelete="CASCADE"), nullable=False)
    Type = db.Column(db.String(12), nullable=False)  # "Minimum" or "Recommended"
    OS = db.Column(db.String(100))
    RAM = db.Column(db.String(50))
    CPU = db.Column(db.String(100))
    GPU = db.Column(db.String(100))
    Storage = db.Column(db.String(50))

    games = db.relationship("Games", back_populates="system_requirements")

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


# def sql_function():
#     categories = {
#     "Minecraft": [6, 7, 8, 13, 4, 11],
#     "Roblox": [6, 10, 11, 7],
#     "Fortnite": [12, 3, 11, 10, 8],
#     "Genshin Impact": [14, 8, 19, 15, 11],
#     "Devil May Cry 5": [1, 18, 17],
#     "Zenless Zone Zero": [1, 14, 19, 24],
#     "Assassin's Creed Shadows": [1, 8, 20, 14, 17],
#     "Grand Theft Auto V": [8, 1, 21, 22, 11],
#     "Diablo III": [14, 18, 23, 4],
#     "Punishing: Gray Raven": [1, 18, 19, 24],
#     "Cyberpunk 2077": [14, 8, 24, 17],
#     "Valorant": [2, 3, 11],
#     "Baldur's Gate 3": [14, 15, 17, 4],
#     "Counter-Strike 2": [2, 3, 11],
#     "League of Legends": [11, 16, 15],
#     "Elden Ring": [14, 8, 15, 1],
#     "Dota 2": [11, 16, 15],
#     "Starfield": [14, 8, 24],
#     "Apex Legends": [2, 12, 11, 24],
#     "God of War Ragnarök": [1, 17, 15, 18],
#     "Spider-Man 2": [1, 8, 17],
#     "The Last of Us Part II": [1, 17, 13],
#     "Horizon Forbidden West": [1, 8, 14, 24],
#     "Final Fantasy XVI": [14, 15, 17, 1],
#     "Demon's Souls [Remake]": [14, 1, 15],
#     "Gran Turismo 7": [22, 9],
#     "Returnal": [1, 24],
#     "Ratchet & Clank: Rift Apart": [1, 5, 24],
#     "Ghost of Tsushima": [1, 8, 20, 17],
#     "Halo Infinite": [2, 3, 11, 24],
#     "Forza Horizon 5": [22, 8, 9],
#     "Wuthering Waves": [1, 14, 8, 19],
#     "Gears 5": [3, 1, 24, 4],
#     "Microsoft Flight Simulator": [9],
#     "Sea of Thieves": [5, 11, 8, 4],
#     "Hellblade II: Senua's Saga": [1, 17, 15],
#     "Fable [Upcoming]": [14, 15, 8],
#     "State of Decay 3": [13, 8, 1],
#     "Avowed [Upcoming]": [14, 15, 8],
#     "Xenoblade Chronicles 3": [14, 15, 19, 17]
#     }

#     sorted_categories = {
#         game: sorted(tags) for game, tags in categories.items()
#     }

#     for i, (game, tags) in enumerate(sorted_categories.items(), start=1):
#         print(i)
#         for tag in tags:
#             print(tag)
#         print("-----")
