import pydantic

from tortoise import Model, fields
from tortoise.contrib.pydantic import pydantic_model_creator

from pydantic import BaseModel
from datetime import datetime



#database for user , business, and proudcts

class User(Model):
    id = fields.IntField(pk = True, index = True)
    username = fields.CharField(max_length=20, null = False, unique = True)
    email = fields.CharField(max_length = 200, null = False, unique = True)
    password = fields.CharField(max_length=100, null = False)
    is_verified = fields.BooleanField(default = False)
    join_date = fields.DatetimeField(default = datetime.utcnow)

class Business(Model):
    id = fields.IntField(pk = True, index = True)
    business_name = fields.CharField(max_length = 20, null = False, unique = True)
    city = fields.CharField(max_length = 100, null = False, default = "Unspecifed")
    region = fields.CharField(max_length = 100, null = False, default = "Unspecified")
    business_description = fields.TextField(null = True)
    logo = fields.CharField(max_length = 200, null = False, default= "default.jpg")
    owner = fields.ForeignKeyField("models.User", related_name = "business")


class Product(Model):
    id = fields.IntField(pk = True, index = True)
    name = fields.CharField(max_length = 100, null = False, unique = True)
    category = fields.CharField(max_length = 30, index = True)
    original_price = fields.DecimalField(max_digits=12, decimal_places=2)
    new_price = fields.DecimalField(max_digits=12, decimal_places=2)
    percentage_discount = fields.IntField()
    offer_expiration_date = fields.DateField(default = datetime.utcnow)
    product_image = fields.CharField(max_length = 200, null = False, default= "ProductDefault.jpg")
    business = fields.ForeignKeyField("models.Business", related_name = "products")


#creating pydatic models
user_pydantic = pydantic_model_creator(User, name = "User", exclude=  ("is_verified",  ))
user_pydanticIn = pydantic_model_creator(User, name = "UserIn", exclude_readonly = True)
user_pydanticOut = pydantic_model_creator(User, name = "UserOut", exclude = ("password", ))

business_pydantic  = pydantic_model_creator(Business, name = "Business")
business_pydanticIn = pydantic_model_creator(Business, name = "BusinessIn", exclude_readonly=True)
produt_pydantic = pydantic_model_creator(Product, name = "Product")
produt_pydanticIn = pydantic_model_creator(Product, name = "ProductIn", exclude = ("percentage_discount", "id"))

