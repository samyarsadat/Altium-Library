"""
    Altium component library parameters database schema.
    Copyright 2026 Samyar Sadat Akhavi

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
"""

import json
import re
from pathlib import Path
from typing import Optional
from unidecode import unidecode
from sqlalchemy import (
    String, Text, ForeignKey, UniqueConstraint, event, create_engine
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, relationship
)
from sqlalchemy.engine import Engine



# Categoties metadata from JSON file
_CATEGORIES_FILE = Path(__file__).with_name("categories.json")
with _CATEGORIES_FILE.open("r", encoding="utf-8") as file:
    CATEGORIES = json.load(file)

# Add normalized column names to category params
def param_normalized(text: str) -> str:
    text = unidecode(text)
    return re.sub(r'[^a-z0-9]+', '_', text.lower()).strip('_')

for category in CATEGORIES:
    category["params"] = [
        (param_name, param_normalized(param_name)) 
        for param_name in category["params"]
    ]

# Alternate views of category metadata
BY_SHEET = {c["sheet"]: c for c in CATEGORIES}
BY_KEY = {c["key"]: c for c in CATEGORIES}



Key = String(255)  # Constrained length for key columns (PK/FK, uniques)
class Base(DeclarativeBase): pass

# -------------------------------------
# Common/shared part parameter tables
# -------------------------------------
class Manufacturer(Base):
    __tablename__ = "manufacturers"
    
    manufacturer_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Key, unique=True)

class Supplier(Base):
    __tablename__ = "suppliers"
    
    supplier_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Key, unique=True)

class Symbol(Base):
    __tablename__ = "symbols"
    __table_args__ = (
        UniqueConstraint("library_ref", "library_path"),
    )
    
    symbol_id: Mapped[int] = mapped_column(primary_key=True)
    library_ref: Mapped[str] = mapped_column(Key)
    library_path: Mapped[str] = mapped_column(Key)

class Footprint(Base):
    __tablename__ = "footprints"
    __table_args__ = (
        UniqueConstraint("footprint_ref", "footprint_path"),
    )
    
    footprint_id: Mapped[int] = mapped_column(primary_key=True)
    footprint_ref: Mapped[str] = mapped_column(Key)
    footprint_path: Mapped[str] = mapped_column(Key)
    

# ---------------------------------------------------
# Common part (component) and part suppliers tables
# ---------------------------------------------------
class Part(Base):
    __tablename__ = "parts"
    
    part_number: Mapped[str] = mapped_column(Key, primary_key=True)
    category: Mapped[str] = mapped_column(Key)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    symbol_id: Mapped[int] = mapped_column(
        ForeignKey("symbols.symbol_id")
    )
    footprint_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("footprints.footprint_id")
    )
    manufacturer_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("manufacturers.manufacturer_id")
    )

    symbol: Mapped[Symbol] = relationship(lazy="joined")
    footprint: Mapped[Optional[Footprint]] = relationship(lazy="joined")
    manufacturer: Mapped[Optional[Manufacturer]] = relationship(lazy="joined")
    
    suppliers: Mapped[list["PartSupplier"]] = relationship(
        back_populates="part", 
        cascade="all, delete-orphan",
        order_by="PartSupplier.rank"
    )

class PartSupplier(Base):
    __tablename__ = "part_suppliers"
    __table_args__ = (
        UniqueConstraint("part_number", "rank"),
    )
    
    part_number: Mapped[str] = mapped_column(
        ForeignKey("parts.part_number"), 
        primary_key=True
    )
    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("suppliers.supplier_id"), 
        primary_key=True
    )
    
    part: Mapped[Part] = relationship(back_populates="suppliers")
    supplier: Mapped[Supplier] = relationship(lazy="joined")

    supplier_part_number: Mapped[str] = mapped_column(Key)
    rank: Mapped[int] = mapped_column(default=1)



# Category-specific parameter tables from JSON config
def params_table_name(key: str) -> str:
    return "params_" + key.lower()

def _make_param_table(cat: dict) -> type:
    attrs: dict = {
        "__tablename__": params_table_name(cat["key"]),
        "__annotations__": {"part_number": Mapped[str]},
        "part_number": mapped_column(Key, 
            ForeignKey("parts.part_number"),
            primary_key=True
        ),
        "part": relationship(Part)
    }
    
    for _, col in cat["params"]:
        attrs[col] = mapped_column(Text, nullable=True)
        attrs["__annotations__"][col] = Mapped[Optional[str]]
    
    return type(cat["key"] + "Params", (Base,), attrs)

PARAM_TABLES: dict[str, type] = {
    cat["key"]: _make_param_table(cat) for cat in CATEGORIES if cat["params"]
}


# DB engine creation util, enables FK constraints for SQLite
def engine_for(url: str) -> Engine:
    engine = create_engine(url)
    
    if engine.dialect.name == "sqlite":
        @event.listens_for(engine, "connect")
        def _fk_on(dbapi_conn, _rec):
            dbapi_conn.execute("PRAGMA foreign_keys=ON")
    
    return engine
