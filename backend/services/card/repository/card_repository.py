from sqlalchemy.orm import Session

from services.card.models.card import Card


class CardRepository:

    def find_cards(
        self,
        db: Session,
        user_id: int,
        card_number: str | None = None,
        last4: str | None = None,
        account_id: int | None = None,
        card_type: str | None = None,
        status: str | None = None,
    ) -> list[Card]:

        query = db.query(Card).filter(
            Card.user_id == user_id
        )

        if card_number:
            query = query.filter(
                Card.card_number == card_number
            )

        if last4:
            query = query.filter(
                Card.card_number.endswith(last4)
            )

        if account_id is not None:
            query = query.filter(
                Card.account_id == account_id
            )

        if card_type:
            query = query.filter(
                Card.card_type == card_type.upper()
            )

        if status:
            query = query.filter(
                Card.status == status.upper()
            )

        return query.all()

    def get_by_id(
        self,
        db: Session,
        user_id: int,
        card_id: int,
    ) -> Card | None:

        return (
            db.query(Card)
            .filter(
                Card.id == card_id,
                Card.user_id == user_id,
            )
            .first()
        )