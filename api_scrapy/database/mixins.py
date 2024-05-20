from sqlalchemy import orm, DateTime, func


class DateTimeMixin:
    created_at = orm.mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at = orm.mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
