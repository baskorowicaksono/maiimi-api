import os
import uvicorn
import asyncio

from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi import FastAPI, HTTPException, status
from fastapi_sqlalchemy import DBSessionMiddleware, db
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from dotenv import load_dotenv
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

from schema import Supply as SchemaSupply
from schema import Produksi as SchemaProduksi
from schema import Penjualan as SchemaPenjualan
from schema import Pembeli as SchemaPembeli
from schema import User as SchemaUser

from schema import SupplyUpdate as SchemaSupplyUpdate
from schema import PenjualanUpdate as SchemaPenjualanUpdate
from schema import PembeliUpdate as SchemaPembeliUpdate

from models import Supply as ModelSupply
from models import Produksi as ModelProduksi
from models import Penjualan as ModelPenjualan
from models import Pembeli as ModelPembeli
from models import User as ModelUser

load_dotenv(".env")

skema_oauth2 = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()
app.add_middleware(DBSessionMiddleware, db_url= os.environ["DATABASE_URL"])

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

async def get_user(username: str):
    found_user = db.session.query(ModelUser).filter(ModelUser.id_username == username).first()
    if found_user is None:
        return False

    return found_user

async def authenticate_user(username: str, password: str):
    user = await asyncio.gather(get_user(username))
    if not user:
        return False
    if not verify_password(password, user[0].password):
        return False
    return user[0]


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = await asyncio.gather(get_user(username=token_data.username))
    if user[0] is None:
        raise credentials_exception
    return user[0]


async def get_current_active_user(current_user: SchemaUser = Depends(get_current_user)):
    if current_user.status == False:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await asyncio.gather(authenticate_user(form_data.username, form_data.password))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user[0].id_username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=SchemaUser)
async def read_users_me(current_user: SchemaUser = Depends(get_current_active_user)):
    return current_user

@app.get("/")
async def landing():
    return {
        "message": "Server Successfully runnning"
    }

# API bagian Supply
@app.get("/get-supplies")
async def get_all_supplies(current_user = Depends(get_current_active_user)):
    supplies = db.session.query(ModelSupply).all()
    if len(supplies) < 1:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No Supplies were found")
    return supplies

@app.get("/get-supply/{supply_id}")
async def get_a_supply(supply_id:str, current_user = Depends(get_current_active_user)):
    found_supply = db.session.query(ModelSupply).filter(ModelSupply.id_produk == supply_id).first()
    if found_supply is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supply not found")
    return found_supply

@app.post("/add-supply", response_model = SchemaSupply, status_code = status.HTTP_201_CREATED)
async def add_supply(supply: SchemaSupply, current_user = Depends(get_current_active_user)):
    db_supply = ModelSupply(
        id_produk=supply.id_produk,
        nama_produk=supply.nama_produk,
        jumlah=supply.jumlah,
        deskripsi=supply.deskripsi,
        jenis=supply.jenis,
        status= "Unavailable" if  supply.jumlah < 1 else ("Available" if supply.jumlah >= 1 else supply.jumlah)
    )

    db.session.add(db_supply)
    db.session.commit()

    return db_supply

@app.put("/update-supply/{supply_id}", response_model = SchemaSupplyUpdate, status_code = status.HTTP_200_OK)
async def update_supply(supply_id: str, supply: SchemaSupplyUpdate, current_user = Depends(get_current_active_user)):
    supply_to_update = db.session.query(ModelSupply).filter(ModelSupply.id_produk == supply_id).first()
    if supply_to_update is None:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "Supply not found")

    supply_to_update.nama_produk = supply.nama_produk
    supply_to_update.jumlah = supply.jumlah
    supply_to_update.deskripsi = supply.deskripsi
    supply_to_update.jenis = supply.jenis
    supply_to_update.status = "Unavailable" if  supply.jumlah < 1 else ("Available" if supply.jumlah >= 1 else supply.jumlah)

    db.session.commit()

    return supply_to_update

@app.delete("/delete-supply/{supply_id}")
async def delete_a_supply(supply_id: str, current_user = Depends(get_current_active_user)):
    supply_to_delete = db.session.query(ModelSupply).filter(ModelSupply.id_produk == supply_id).first()
    if supply_to_delete is None:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "Supply not found")

    db.session.delete(supply_to_delete)
    db.session.commit()

    return {
        "message" : f"Supply {supply_id} successfully deleted"
    }

@app.delete("/delete-supplies")
async def delete_supplies(current_user = Depends(get_current_active_user)):
    supplies = db.session.query(ModelSupply).all()

    if len(supplies) == 0:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "No Supplies were found")

    for supply in supplies:
        db.session.delete(supply)
        db.session.commit()

    return {
        "message" : "All supplies successfully deleted"
    }

# API bagian Produksi
@app.get("/get-productions")
async def get_all_productions(current_user = Depends(get_current_active_user)):
    productions = db.session.query(ModelProduksi).all()
    if len(productions) < 1:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No Productions were found")
    return productions

@app.get("/get-production/{production_id}")
async def get_a_production(production_id:str, current_user = Depends(get_current_active_user)):
    found_production = db.session.query(ModelProduksi).filter(ModelProduksi.id_produksi == production_id).first()
    if found_production is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Production not found")
    return found_production

@app.post("/add-production", response_model=SchemaProduksi, status_code=status.HTTP_201_CREATED)
async def add_production(produksi: SchemaProduksi, current_user = Depends(get_current_active_user)):
    try:
        db_produksi = ModelProduksi(
            id_produksi=produksi.id_produksi,
            status_produksi = produksi.status_produksi,
            id_produk = produksi.id_produk
        )

        db.session.add(db_produksi)
        db.session.commit()

        return db_produksi
    except:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product ID Not found")

@app.delete("/delete-productions")
async def delete_all_productions(current_user = Depends(get_current_active_user)):
    productions = db.session.query(ModelProduksi).all()
    if len(productions) == 0:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "No Productions were found")

    for produksi in productions:
        db.session.delete(produksi)
        db.session.commit()

    return {
        "message" : "All production successfully deleted"
    }

@app.delete("/delete-production/{production_id}")
async def delete_production(production_id: str, current_user = Depends(get_current_active_user)):
    production_to_delete = db.session.query(ModelProduksi).filter(ModelProduksi.id_produksi == production_id).first()

    if production_to_delete is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Production not found")

    db.session.delete(production_to_delete)
    db.session.commit()

    return {
        "message" : f"Production {production_id} successfully deleted"
    }

# API bagian Penjualan
@app.get("/get-sellings")
async def get_all_sellings(current_user = Depends(get_current_active_user)):
    sellings = db.session.query(ModelPenjualan).all()
    if len(sellings) < 1:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No Sellings were found")
    return sellings

@app.get("/get-selling/{selling_id}")
async def get_a_selling(selling_id:str, current_user = Depends(get_current_active_user)):
    found_selling = db.session.query(ModelPenjualan).filter(ModelPenjualan.id_transaksi == selling_id).first()
    if found_selling is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Selling not found")
    return found_selling

@app.post("/add-selling", response_model = SchemaPenjualan, status_code = status.HTTP_201_CREATED)
async def add_penjualan(penjualan: SchemaPenjualan, current_user = Depends(get_current_active_user)):
    db_penjualan = ModelPenjualan(
        id_transaksi=penjualan.id_transaksi,
        jumlah_penjualan=penjualan.jumlah_penjualan,
        pendapatan=penjualan.pendapatan,
        status=penjualan.status
    )

    db.session.add(db_penjualan)
    db.session.commit()

    return db_penjualan

@app.put("/update-selling/{selling_id}", response_model = SchemaPenjualanUpdate, status_code = status.HTTP_200_OK)
async def update_penjualan(selling_id: str, penjualan: SchemaPenjualanUpdate, current_user = Depends(get_current_active_user)):
    penjualan_to_update = db.session.query(ModelPenjualan).filter(ModelPenjualan.id_transaksi == selling_id).first()

    if penjualan_to_update is None:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "Penjualan not found")

    penjualan_to_update.jumlah_penjualan = penjualan.jumlah_penjualan
    penjualan_to_update.pendapatan = penjualan.pendapatan
    penjualan_to_update.status = penjualan.status

    db.session.commit()

    return penjualan_to_update

@app.delete("/delete-selling/{selling_id}")
async def delete_a_penjualan(selling_id: str, current_user = Depends(get_current_active_user)):
    penjualan_to_delete = db.session.query(ModelPenjualan).filter(ModelPenjualan.id_transaksi == selling_id).first()

    if penjualan_to_delete is None:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "Penjualan not found")

    db.session.delete(penjualan_to_delete)
    db.session.commit()

    return {
        "message" : f"Penjualan {selling_id} successfully deleted"
    }

@app.delete("/delete-sellings")
async def delete_penjualan(current_user = Depends(get_current_active_user)):
    penjualan = db.session.query(ModelPenjualan).all()

    if len(penjualan) == 0:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "No sellings were found")

    for item in penjualan:
        db.session.delete(item)
        db.session.commit()

    return {
        "message" : "All sellings successfully deleted"
    }


# API bagian pembeli
@app.get("/get-buyers")
async def get_all_buyers(current_user = Depends(get_current_active_user)):
    buyers = db.session.query(ModelPembeli).all()
    if len(buyers) < 1:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail="No Buyers were found")
    return buyers

@app.get("/get-buyer/{buyer_id}")
async def get_a_buyer(buyer_id:str, current_user = Depends(get_current_active_user)):
    found_buyer = db.session.query(ModelPembeli).filter(ModelPembeli.id_pembeli == buyer_id).first()
    if found_buyer is None:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail="Buyer not found")
    return found_buyer

@app.post("/add-buyer", response_model = SchemaPembeli, status_code = status.HTTP_201_CREATED)
async def add_buyer(pembeli: SchemaPembeli, current_user = Depends(get_current_active_user)):
    db_pembeli = ModelPembeli(
        id_pembeli=pembeli.id_pembeli,
        nama_pembeli=pembeli.nama_pembeli,
        umur=pembeli.umur,
        gender=pembeli.gender,
        alamat=pembeli.alamat,
        no_telp=pembeli.no_telp,
        email=pembeli.email
    )

    db.session.add(db_pembeli)
    db.session.commit()

    return db_pembeli

@app.put("/update-buyer/{buyer_id}", response_model = SchemaPembeliUpdate, status_code = status.HTTP_200_OK)
async def update_buyer(buyer_id: str, pembeli: SchemaPembeliUpdate, current_user = Depends(get_current_active_user)):
    pembeli_to_update = db.session.query(ModelPembeli).filter(ModelPembeli.id_pembeli == buyer_id).first()

    if pembeli_to_update is None:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "Buyer not found")

    pembeli_to_update.nama_pembeli = pembeli.nama_pembeli
    pembeli_to_update.umur = pembeli.umur
    pembeli_to_update.gender = pembeli.gender
    pembeli_to_update.alamat = pembeli.alamat
    pembeli_to_update.no_telp = pembeli.no_telp
    pembeli_to_update.email = pembeli.email

    db.session.commit()

    return pembeli_to_update

@app.delete("/delete-buyer/{buyer_id}")
async def delete_a_buyer(buyer_id: str, current_user = Depends(get_current_active_user)):
    pembeli_to_delete = db.session.query(ModelPembeli).filter(ModelPembeli.id_pembeli == buyer_id).first()

    if pembeli_to_delete is None:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "Buyer not found")

    db.session.delete(pembeli_to_delete)
    db.session.commit()

    return {
        "message" : f"Buyer {buyer_id} successfully deleted"
    }

@app.delete("/delete-buyers")
async def delete_all_buyer(current_user = Depends(get_current_active_user)):
    pembeli = db.session.query(ModelPembeli).all()

    if len(pembeli) == 0:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "No sellings were found")

    for item in pembeli:
        db.session.delete(item)
        db.session.commit()

    return {
        "message" : "All buyers successfully deleted"
    }


# API bagian user
@app.get("/get-users")
async def get_users(current_user = Depends(get_current_active_user)):
    users = db.session.query(ModelUser).all()
    if len(users) < 1:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail="No Users were found")
    return users

@app.get("/get-user/{username}")
async def get_user(username:str, current_user = Depends(get_current_active_user)):
    found_user = db.session.query(ModelUser).filter(ModelUser.id_username == username).first()
    if found_user is None:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail="User not found")
    return found_user

@app.post("/add-user", response_model=SchemaUser, status_code = status.HTTP_201_CREATED)
async def add_user(user: SchemaUser, current_user = Depends(get_current_active_user)):
    db_user = ModelUser(
        id_username=user.id_username,
        password=get_password_hash(user.password),
        role = user.role,
        email=user.email,
        status = user.status
    )

    db.session.add(db_user)
    db.session.commit()

    return db_user

if __name__ == "__main__":
    uvicorn.run(app, host= "0.0.0.0", port=8000, reload=True)
