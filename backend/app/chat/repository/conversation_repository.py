from sqlalchemy.orm import Session

from app.chat.models.conversations import Conversation


class ConversationRepository:

    def create(
        self,
        db: Session,
        user_id: int,
    ):
        conversation = Conversation(
            user_id=user_id,
        )

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        return conversation

    def get_by_id(
        self,
        db: Session,
        conversation_id: int,
    ):
        return (
            db.query(Conversation)
            .filter(
                Conversation.id == conversation_id
            )
            .first()
        )

    def get_by_user(
        self,
        db: Session,
        user_id: int,
    ):
        return (
            db.query(Conversation)
            .filter(
                Conversation.user_id == user_id
            )
            .order_by(
                Conversation.updated_at.desc()
            )
            .all()
        )