import uuid
from sqlalchemy import Column, String, Integer, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from geoalchemy2 import Geometry
from app.db.base import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    name = Column(
        String,
        nullable=False
    )

    aoi = Column(
        Geometry("POLYGON", srid=4326),
        nullable=False
    )

    year = Column(
        Integer,
        nullable=False
    )

    months = Column(
        ARRAY(Integer),
        nullable=False
    )

    cloud = Column(
        Integer,
        default=20
    )

    status = Column(
        String,
        nullable=False,
        default="draft"
    )

    created_at = Column(
        TIMESTAMP,
        nullable=False,
        server_default=text("NOW()")
    )
