from enum import Enum

from sqlalchemy.orm import Session

from services.card.repository.card_repository import (
    CardRepository,
)


class CardResolutionStatus(str, Enum):
    FOUND = "FOUND"
    NOT_FOUND = "NOT_FOUND"
    AMBIGUOUS = "AMBIGUOUS"
    INVALID = "INVALID"


class CardService:

    def __init__(self):
        self.repository = CardRepository()

    # =====================================================
    # CARD RESOLUTION
    # =====================================================

    def resolve_card(
        self,
        db: Session,
        user_id: int,
        card_number: str | None = None,
        last4: str | None = None,
        account_id: int | None = None,
        card_type: str | None = None,
    ) -> dict:

        # ---------------------------------------------
        # Validate last4
        # ---------------------------------------------

        if last4 is not None:

            if (
                not last4.isdigit()
                or len(last4) != 4
            ):
                return {
                    "status": (
                        CardResolutionStatus.INVALID.value
                    ),
                    "message": (
                        "Invalid card identifier."
                    ),
                }

        # ---------------------------------------------
        # Find cards
        # ---------------------------------------------

        cards = self.repository.find_cards(
            db=db,
            user_id=user_id,
            card_number=card_number,
            last4=last4,
            account_id=account_id,
            card_type=card_type,
        )

        # ---------------------------------------------
        # Not found
        # ---------------------------------------------

        if not cards:

            return {
                "status": (
                    CardResolutionStatus.NOT_FOUND.value
                ),
                "message": "Card not found.",
            }

        # ---------------------------------------------
        # Multiple matches
        # ---------------------------------------------

        if len(cards) > 1:

            return {
                "status": (
                    CardResolutionStatus.AMBIGUOUS.value
                ),
                "message": "Multiple cards match.",
                "cards": [
                    self._masked_card(card)
                    for card in cards
                ],
            }

        # ---------------------------------------------
        # Exactly one
        # ---------------------------------------------

        return {
            "status": CardResolutionStatus.FOUND.value,
            "card": cards[0],
        }

    # =====================================================
    # LIST
    # =====================================================

    def list_cards(
        self,
        db: Session,
        user_id: int,
        account_id: int | None = None,
        status: str | None = None,
    ) -> list[dict]:

        cards = self.repository.find_cards(
            db=db,
            user_id=user_id,
            account_id=account_id,
            status=status,
        )

        return [
            self._format_card(card)
            for card in cards
        ]

    # =====================================================
    # GET CARD BY ID
    # =====================================================

    def get_card(
        self,
        db: Session,
        user_id: int,
        card_id: int,
    ) -> dict:

        card = self.repository.get_by_id(
            db=db,
            user_id=user_id,
            card_id=card_id,
        )

        if card is None:

            return {
                "status": "NOT_FOUND",
                "message": "Card not found.",
            }

        return {
            "status": "FOUND",
            "card": self._format_card(card),
        }

  
    # =====================================================
    # DETAILS
    # =====================================================

    def get_details(
        self,
        db: Session,
        user_id: int,
        card_number: str | None = None,
        last4: str | None = None,
        account_id: int | None = None,
        card_type: str | None = None,
    ) -> dict:

        result = self.resolve_card(
            db=db,
            user_id=user_id,
            card_number=card_number,
            last4=last4,
            account_id=account_id,
            card_type=card_type,
        )

        if result["status"] != (
            CardResolutionStatus.FOUND.value
        ):
            return result

        return {
            "status": "FOUND",
            "card": self._format_card(
                result["card"]
            ),
        }

    # =====================================================
    # STATUS
    # =====================================================

    def get_status(
        self,
        db: Session,
        user_id: int,
        card_number: str | None = None,
        last4: str | None = None,
        account_id: int | None = None,
        card_type: str | None = None,
    ) -> dict:

        result = self.resolve_card(
            db=db,
            user_id=user_id,
            card_number=card_number,
            last4=last4,
            account_id=account_id,
            card_type=card_type,
        )

        if result["status"] != (
            CardResolutionStatus.FOUND.value
        ):
            return result

        card = result["card"]

        return {
            "status": "FOUND",
            "card_id": card.id,
            "last4": card.card_number[-4:],
            "card_status": card.status,
        }

    # =====================================================
    # LIMITS
    # =====================================================

    def get_limits(
        self,
        db: Session,
        user_id: int,
        card_number: str | None = None,
        last4: str | None = None,
        account_id: int | None = None,
        card_type: str | None = None,
    ) -> dict:

        result = self.resolve_card(
            db=db,
            user_id=user_id,
            card_number=card_number,
            last4=last4,
            account_id=account_id,
            card_type=card_type,
        )

        if result["status"] != (
            CardResolutionStatus.FOUND.value
        ):
            return result

        card = result["card"]

        return {
            "status": "FOUND",
            "card_id": card.id,
            "last4": card.card_number[-4:],
            "daily_purchase_limit": float(
                card.daily_purchase_limit
            ),
            "daily_atm_limit": float(
                card.daily_atm_limit
            ),
        }

    # =====================================================
    # FREEZE CARD
    # =====================================================

    def freeze_card(
        self,
        db: Session,
        user_id: int,
        card_number: str | None = None,
        last4: str | None = None,
        execute: bool = False,
    ) -> dict:

        # ---------------------------------------------
        # Resolve card
        # ---------------------------------------------

        result = self.resolve_card(
            db=db,
            user_id=user_id,
            card_number=card_number,
            last4=last4,
        )
        print("[CARD DEUBUG]",result)
        if result["status"] != (
            CardResolutionStatus.FOUND.value
        ):
            return result

        card = result["card"]

        # ---------------------------------------------
        # Already frozen
        # ---------------------------------------------

        if card.status == "FROZEN":

            return {
                "status": "ALREADY_FROZEN",
                "card_id": card.id,
                "last4": card.card_number[-4:],
            }

        # ---------------------------------------------
        # Execute approved action
        # ---------------------------------------------

        if execute:

            card.status = "FROZEN"

            db.commit()

            db.refresh(card)

            return {
                "status": "FROZEN",
                "card_id": card.id,
                "last4": card.card_number[-4:],
            }

        # ---------------------------------------------
        # Approval required
        # ---------------------------------------------

        return {
            "status": "APPROVAL_REQUIRED",
            "action": "freeze_card",
            "card_id": card.id,
            "last4": card.card_number[-4:],
            "message": (
                f"Freeze card ending in "
                f"{card.card_number[-4:]}?"
            ),
            "description": (
                "This action will temporarily "
                "disable the card."
            ),
        }

    # =====================================================
    # UNFREEZE CARD
    # =====================================================

    def unfreeze_card(
        self,
        db: Session,
        user_id: int,
        card_number: str | None = None,
        last4: str | None = None,
        execute: bool = False,
    ) -> dict:

        # ---------------------------------------------
        # Resolve card
        # ---------------------------------------------

        result = self.resolve_card(
            db=db,
            user_id=user_id,
            card_number=card_number,
            last4=last4,
        )

        if result["status"] != (
            CardResolutionStatus.FOUND.value
        ):
            return result

        card = result["card"]

        # ---------------------------------------------
        # Already active
        # ---------------------------------------------

        if card.status == "ACTIVE":

            return {
                "status": "ALREADY_UNFROZEN",
                "card_id": card.id,
                "last4": card.card_number[-4:],
            }

        # ---------------------------------------------
        # Invalid state
        # ---------------------------------------------

        if card.status != "FROZEN":

            return {
                "status": "INVALID_STATE",
                "card_id": card.id,
                "last4": card.card_number[-4:],
                "message": (
                    "Card cannot be unfrozen from "
                    "its current state."
                ),
            }

        # ---------------------------------------------
        # Execute approved action
        # ---------------------------------------------

        if execute:

            card.status = "ACTIVE"

            db.commit()

            db.refresh(card)

            return {
                "status": "UNFROZEN",
                "card_id": card.id,
                "last4": card.card_number[-4:],
            }

        # ---------------------------------------------
        # Approval required
        # ---------------------------------------------

        return {
            "status": "APPROVAL_REQUIRED",
            "action": "unfreeze_card",
            "card_id": card.id,
            "last4": card.card_number[-4:],
            "message": (
                f"Unfreeze card ending in "
                f"{card.card_number[-4:]}?"
            ),
            "description": (
                "This action will reactivate the card."
            ),
        }

    # =====================================================
    # RESPONSE HELPERS
    # =====================================================

    def _masked_card(
        self,
        card,
    ) -> dict:

        return {
            "card_id": card.id,
            "last4": card.card_number[-4:],
            "card_type": card.card_type,
            "status": card.status,
        }

    def _format_card(
        self,
        card,
    ) -> dict:

        return {
            "card_id": card.id,
            "last4": card.card_number[-4:],
            "card_type": card.card_type,
            "status": card.status,
            "account_id": card.account_id,
            "expiry_date": card.expiry_date.strftime(
                "%m/%Y"
            ),
            "daily_purchase_limit": float(
                card.daily_purchase_limit
            ),
            "daily_atm_limit": float(
                card.daily_atm_limit
            ),
        }