from sqlalchemy.orm import Session

from app.chat.models.messages import Message


class MessageRepository:

    def create(
        self,
        db: Session,
        conversation_id: int,
        role: str,
        content: str,
    ):

        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )

        db.add(message)
        db.commit()
        db.refresh(message)

        return message

    def get_by_id(
        self,
        db: Session,
        message_id: int,
    ):

        return (
            db.query(Message)
            .filter(
                Message.id == message_id
            )
            .first()
        )

    def get_by_conversation(
        self,
        db: Session,
        conversation_id: int,
    ):

        return (
            db.query(Message)
            .filter(
                Message.conversation_id
                == conversation_id
            )
            .order_by(
                Message.created_at.asc()
            )
            .all()
        )