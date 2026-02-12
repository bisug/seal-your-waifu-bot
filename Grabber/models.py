from umongo import Document, fields, EmbeddedDocument
from Grabber.database import instance

@instance.register
class Character(Document):
    id = fields.StringField(required=True, unique=True)
    name = fields.StringField(required=True)
    anime = fields.StringField(required=True)
    rarity = fields.StringField(required=True)
    img_url = fields.StringField(required=True)
    zenith_price = fields.IntegerField(default=5)
    sold_count = fields.IntegerField(default=0)

    class Meta:
        collection_name = "anime_characterss"

@instance.register
class UserCharacter(EmbeddedDocument):
    id = fields.StringField(required=True)
    name = fields.StringField(required=True)
    anime = fields.StringField(required=True)
    rarity = fields.StringField(required=True)
    img_url = fields.StringField(required=True)

@instance.register
class User(Document):
    id = fields.IntegerField(required=True, unique=True)
    zenith = fields.IntegerField(default=0)
    characters = fields.ListField(fields.EmbeddedField(UserCharacter), default=[])

    class Meta:
        collection_name = "user_collectionsss"
