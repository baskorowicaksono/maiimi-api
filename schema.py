from pydantic import BaseModel
from typing import Optional

class Supply(BaseModel):
    id_produk: str
    nama_produk: str
    jumlah: int
    deskripsi: Optional[str] = None
    jenis: str
    status: Optional[str] = "Unavailable"

    class Config:
        orm_mode = True

class SupplyUpdate(BaseModel):
    nama_produk: str
    jumlah: int
    deskripsi: Optional[str] = None
    jenis: str
    status: str

    class Config:
        orm_mode = True

class Produksi(BaseModel):
    id_produksi: str
    status_produksi: str
    id_produk: str

    class Config:
        orm_mode = True


class Penjualan(BaseModel):
    id_transaksi: str
    jumlah_penjualan: int
    pendapatan: int
    status: int

    class Config:
        orm_mode = True

class PenjualanUpdate(BaseModel):
    jumlah_penjualan: int
    pendapatan: int
    status: int

    class Config:
        orm_mode = True

class Pembeli(BaseModel):
    id_pembeli: str
    nama_pembeli: str
    umur: Optional[int] = None
    gender: Optional[str] = None
    alamat: str
    no_telp:str
    email: str

    class Config:
        orm_mode = True

class PembeliUpdate(BaseModel):
    nama_pembeli: str
    umur: Optional[int] = None
    gender: Optional[str] = None
    alamat: str
    no_telp:str
    email: str

    class Config:
        orm_mode = True

class User(BaseModel):
    id_username: str
    password: str
    email: str
    role: str
    status: Optional[bool] = True

    class Config:
        orm_mode = True