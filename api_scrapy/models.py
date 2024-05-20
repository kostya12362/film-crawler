import random
import string
import uuid

from sqlalchemy import orm, Index, UniqueConstraint

from .database import Model, DateTimeMixin


def generate_key(length: int = 32) -> str:
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


class Token(Model, DateTimeMixin):
    __tablename__ = 'tokens'
    id: orm.Mapped[uuid.UUID] = orm.mapped_column(primary_key=True, autoincrement=True)
    name: orm.Mapped[str] = orm.mapped_column(nullable=False)
    token: orm.Mapped[str] = orm.mapped_column(nullable=False, default=generate_key)
    is_active: orm.Mapped[bool] = orm.mapped_column(nullable=False, default=True)

    __table_args__ = (
        Index("idx_name_and_id", id, name, unique=True),
        UniqueConstraint(id, name, name='idx_name_and_id'),
    )

    def __str__(self):
        return self.name
