from fastapi import (FastAPI,BackgroundTasks, UploadFile, File, From, Depends, HTTPException, status, Request)
from tortoise import models
from tortoise.contrib.fastapi import register_tortoise
from models import(User, Business, Product, user_pydantic, user_pydanticIn,produt_pydantic, produt_pydanticIn, business_pydantic, business_pydanticIn, user_pydanticOut)
from authentication import (get_hashed_password)
from emails import send_email
#signals 
from tortoise.signals import post_save
from typing import List, Optional, Type
from tortoise import BaseDBAsyncClient

from starlette.responses import JSONResponce
from starlette.requests import Request

#Authentication, and Authorization

import jwt
from dotenv import dotenv_values
from fastapi.security import(OAuth2PasswordBearer, OAuth2PasswordRequestForm)

#self packages

from emails import *
from authentication import *
import math


#user images uploads
#pip install python_multipart

from fastapi.staticfiles import StaticFiles

#pillow
from PIL import Image

#tempaltes
from fastapi.templating import Jinja2Templates


#html responce
from fastapi.responses import HTMLResponse


config_credentials = dict(dotenv_values(".env"))


app = FastAPI(User)

#static files
#pip install aioflies

app.mount("/static", StaticFiles(directory="static"), name = "static")


#authorization configs
oath2_scheme = OAuth2PasswordBearer(tokenUrl = 'token')


#pass word helper functions
@app.post("/token")
async def generate_token(request_form:OAuth2PasswordRequestForm = Depends()):
    token = await token_generator(request_form.username, request_form.password)
    return {'access_token':token, 'token_type':'bearer'}


# process signals here
@post_save(User)
async def create_business(
    sender: "Type[User]",
    instance: User,
    created: bool,
    using_db: "Optional[BaseDBAsyncClient]",
    update_fields: List[str]) -> None:
    
    if created:
        business_obj = await Business.create(
                business_name = instance.username, owner = instance)
        await business_pydantic.from_tortoise_orm(business_obj)
        # send email functionality
        await send_email([instance.email], instance)
             
        
@app.post("/registration")
async def user_registration(user: user_pydanticIn):
    user_info = user.dict(exclude_unset = True)
    user_info["password"] = get_password_hash(user_info["password"])
    user_obj = await User.create(**user_info)
    new_user = await user_pydantic.from_tortoise_orm(user_obj)
    return{
            "status":"ok",
            "data":f"Hello {new_user.username} thanks for choosing our services. Please
            check your email inbox and click on the link to confirm your registration"
    }

#tempalte for email verification

templates = Jinja2Templates(directory="tempaltes")



@app.get('/verification', responce_class=HTMLResponse)
#Make sure to import request from fastapi and HTMLResponce
async def email_verification(request: Request, token: str):
    user = await verify_token(token)
    if user and not user.is_verified:
        user.is_verified = True
        await user.save()
        return templates.TemplateResponce("verifcation.html", {"request":request, "username":user.username})
    

    raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED,
                        detail = "Invalid or expired token",
                        headers = {"WWW-Authenticate": "Bearer"},
                        )

async def get_current_user(token: str = Depends(oath2_scheme)):
    try:
        payload = jwt.decode(token, config_credentials['SECRET'], algorithms = ['HS256'])
        user = await User.get(id = payload.get("id"))
    except:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid username or password",
            headers = {"WWW-Authenticate": "Bearer"},
        )
    return await user



@app.post('/user/me')
async def user_login(user: user_pydantic = Depends(get_current_user)):
    business = await Business.get(owner = user)
    business = business.logo
    logo = "localhost:8000/static/images/"+logo

    return {"status": "ok",
            "data": 
            {
                "username" : user.username,
                    "email" : user.email,
                    "verified" : user.is_verified,
                    "join_date" : user.join_date.strftime("%b %d %Y"),
                    "logo" : logo

            }}


@app.post('/products')
async def add_new_product(product: product_pydanticIn, user:user_pydantic = Depends(get_current_user)):
    product = product.dict(exclude_unset = True)
    #to avoid division by zero error

    if product['original_price'] > 0:
        product["percentage_discount"] = ((product["original_price"] - product["new_price"])/product['original_price']) * 100

    
    product_obj = await Product.create(**product, business = user)
    product_obj = await product_pydantic.from_tortoise_orm(product_obj)
    return {"status":"ok", "data":product_obj}


@app.get('/products')
async def get_products():
    responce = await product_pydantic.from_tortoise_orm(Product.all())
    return {"status": "ok", "data": responce}


@app.get('/products/{id}')
async def specific_product(id: int):
    product = await Product.get(id = id)
    business = await product.business
    owner = await business.owner
    responce = await product_pydantic.from_queryset_single(Product.get(id = id))
    print(type(responce))
    return {"status": "ok",
            "data":
            {
                        "product_details" : responce,
                        "business_details" : {
                            "name" : business.business_name,
                            "city" : business.city,
                            "region" : business.region,
                            "description" : business.business_description,
                            "logo" : business.logo,
                            "owner_id" : owner.id,
                            "email" : owner.email,
                            "join_date" :  owner.join_date.strftime("%b %d %Y")

            }
            }
    }


@app.get("/")
def index():
    return {"Message ": "hello world"}


register_tortoise(
    app,
    db_url = "sqlite://database.sqlite3",
    modules = {"models": ["models"]},
    generate_schemas = True,
    add_exception_handlers = True
)