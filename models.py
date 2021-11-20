from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

# model untuk tabel Supply
class Supply(Base):
    __tablename__ = 'supply'
    id_produk = Column(String(8), primary_key=True, index=True)
    nama_produk = Column(String(50), nullable=False, unique=True)
    jumlah = Column(Integer, nullable=False)
    deskripsi = Column(Text, nullable=True)
    jenis = Column(String(25), nullable=False)
    status = Column(String(11), nullable=False, server_default="Unavailable")
    time_created = Column(DateTime(timezone=True), server_default= func.now())
    time_updated = Column(DateTime(timezone=True), onupdate= func.now())

# model untuk tabel produksi
class Produksi(Base):
    __tablename__ = "produksi"
    id_produksi = Column(String(8), primary_key=True, index=True)
    status_produksi = Column(String(15), nullable=False)
    tanggal_produksi = Column(DateTime(timezone=True), nullable=False, server_default= func.now())
    id_produk = Column(String(8), ForeignKey("supply.id_produk"), nullable=False)

    supply = relationship("Supply")

# model untuk tabel penjualan
class Penjualan(Base):
    __tablename__ = "penjualan"
    id_transaksi = Column(String(8), primary_key=True, index=True)
    jumlah_penjualan = Column(Integer, nullable=False)
    pendapatan = Column(Integer, nullable=False)
    status = Column(String(10), nullable=False, server_default="Processed")
    waktu_penjualan = Column(DateTime(timezone=True), server_default=func.now())
    waktu_pengiriman = Column(DateTime(timezone=True), onupdate= func.now())

# model untuk tabel pembeli
class Pembeli(Base):
    __tablename__ = 'pembeli'
    id_pembeli = Column(String(8), primary_key=True, index=True)
    nama_pembeli = Column(String(50), nullable=False)
    umur = Column(Integer, nullable=True)
    gender = Column(String(10), nullable=True)
    alamat = Column(Text, nullable=False)
    no_telp = Column(String(20), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    time_created = Column(DateTime(timezone=True), server_default= func.now())
    time_updated = Column(DateTime(timezone=True), onupdate= func.now())


# Model untuk tabel user
class User(Base):
    __tablename__ = "user"
    id_username = Column(String(20), primary_key=True, index=True)
    password = Column(String(60), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    role = Column(String(15), nullable=False)
    status = Column(Boolean, nullable=False, server_default="true")
    time_created = Column(DateTime(timezone=True), server_default= func.now())
    time_updated = Column(DateTime(timezone=True), onupdate= func.now())