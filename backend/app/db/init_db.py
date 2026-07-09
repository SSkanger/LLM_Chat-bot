from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.database import Base, SessionLocal, engine
from app.db.models import ModelConfig, PromptRole


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_defaults(db)


def seed_defaults(db: Session) -> None:
    settings = get_settings()
    for role in settings.prompt_roles:
        existing = db.query(PromptRole).filter(PromptRole.name == role.name).first()
        if existing:
            existing.description = role.description
            existing.system_prompt = role.system_prompt
        else:
            db.add(
                PromptRole(
                    name=role.name,
                    description=role.description,
                    system_prompt=role.system_prompt,
                )
            )

    for model in settings.models:
        existing = db.query(ModelConfig).filter(ModelConfig.name == model.name).first()
        values = model.model_dump()
        if existing:
            for key, value in values.items():
                setattr(existing, key, value)
        else:
            db.add(ModelConfig(**values))
    db.commit()


if __name__ == "__main__":
    init_db()

