from sqlmodel import Session, select
from app.db import engine
from app.models import User
from app.security import hash_password


def main() -> None:
    email = "sieunhan2038@gmail.com"
    new_password = "852456Nhan"

    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email)).first()
        if not user:
            print("User not found for email:", email)
        else:
            user.password_hash = hash_password(new_password)
            session.add(user)
            session.commit()
            print("Password updated for:", email)


if __name__ == "__main__":
    main()
