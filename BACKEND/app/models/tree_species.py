from sqlalchemy import Column, Integer, Text, Numeric, TIMESTAMP
from sqlalchemy.sql import func

from app.db.base import Base


class TreeSpecies(Base):
    __tablename__ = "tree_species"

    id = Column(Integer, primary_key=True)

    local_name = Column(Text, nullable=False)
    scientific_name = Column(Text, nullable=False)

    description = Column(Text, nullable=True)

    biomass_formula = Column(Text, nullable=False)
    wood_density = Column(Numeric, nullable=True)

    # FOTO
    leaf_photo_url = Column(Text, nullable=True)
    trunk_photo_url = Column(Text, nullable=True)
    tree_photo_url = Column(Text, nullable=True)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
