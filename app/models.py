from app.routes import db

# Many-to-many Relationship Table
PizzaTopping = db.Table('PizzaTopping',
    db.Column('PizzaID', db.Integer, db.ForeignKey('Pizza.PizzaID')),  # noqa E128
    db.Column('ToppingID', db.Integer, db.ForeignKey('Topping.ToppingID'))
)  # noqa: E501


class Pizza(db.Model):
    __tablename__ = "Pizza"
    id = db.Column(db.Integer, primary_key = True)  # noqa
    name = db.Column(db.String())
    description = db.Column(db.Text())
    base = db.Column(db.Integer, db.ForeignKey('Base.BaseID'))

    base_name = db.relationship("Base", backref = "pizzas_with_this_base")  # noqa

    def __repr__(self):
        return f'{self.name.upper()} PIZZA'
