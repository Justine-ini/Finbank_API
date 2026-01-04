from datetime import date
from fastapi import HTTPException, status


def validate_id_dates(issue_date: date, expiry_date: date) -> None:
    if expiry_date <= issue_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "message": "The expiry date of the identification document must be later than its issue date."
            },
        )