from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Member(db.Model):
    __tablename__ = "members"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)

    loans = db.relationship("Loan", back_populates="member", cascade="all, delete-orphan")

    def active_loans_count(self) -> int:
        return sum(1 for loan in self.loans if loan.is_active)


class Duck(db.Model):
    __tablename__ = "ducks"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="available")

    loans = db.relationship("Loan", back_populates="duck", cascade="all, delete-orphan")

    @property
    def is_available(self) -> bool:
        return self.status == "available"


class Loan(db.Model):
    __tablename__ = "loans"

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey("members.id"), nullable=False)
    duck_id = db.Column(db.Integer, db.ForeignKey("ducks.id"), nullable=False)
    borrowed_on = db.Column(db.Date, nullable=False, default=date.today)
    due_on = db.Column(db.Date, nullable=False)

    member = db.relationship("Member", back_populates="loans")
    duck = db.relationship("Duck", back_populates="loans")

    @property
    def is_active(self) -> bool:
        return self.due_on >= date.today()

    @classmethod
    def create(cls, member_id: int, duck_id: int) -> Optional["Loan"]:
        duck = db.session.get(Duck, duck_id)
        if duck is None or not duck.is_available:
            return None

        loan = cls(
            member_id=member_id,
            duck_id=duck_id,
            borrowed_on=date.today(),
            due_on=date.today() + timedelta(days=7),
        )
        db.session.add(loan)
        duck.status = "on loan"
        db.session.commit()
        return loan


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "rubber-duck-secret"
    db.init_app(app)

    @app.route("/")
    def index():
        ducks = Duck.query.order_by(Duck.id).all()
        members = Member.query.order_by(Member.id).all()
        loans = Loan.query.order_by(Loan.borrowed_on.desc(), Loan.id.desc()).all()
        return render_template("index.html", ducks=ducks, members=members, loans=loans)

    @app.route("/checkout", methods=["POST"])
    def checkout():
        member_id = request.form.get("member_id", type=int)
        duck_id = request.form.get("duck_id", type=int)

        if member_id is None or duck_id is None:
            flash("Member and duck are required.")
            return redirect(url_for("index"))

        member = db.session.get(Member, member_id)
        duck = db.session.get(Duck, duck_id)
        if member is None or duck is None:
            flash("Invalid member or duck selection.")
            return redirect(url_for("index"))

        loan = Loan.create(member_id=member.id, duck_id=duck.id)
        if loan is None:
            flash(f"Duck '{duck.name}' is not available right now.")
        else:
            flash(f"Checked out '{duck.name}' to {member.name}. Due on {loan.due_on.isoformat()}.")
        return redirect(url_for("index"))

    @app.route("/return/<int:loan_id>", methods=["POST"])
    def return_duck(loan_id: int):
        loan = db.session.get(Loan, loan_id)
        if loan is None:
            flash("That loan does not exist.")
            return redirect(url_for("index"))

        loan.duck.status = "available"
        db.session.delete(loan)
        db.session.commit()
        flash(f"Returned '{loan.duck.name}' and closed the loan record.")
        return redirect(url_for("index"))

    with app.app_context():
        db.create_all()
        if Member.query.first() is None:
            members = [Member(name="Ada"), Member(name="Grace"), Member(name="Linus")]
            ducks = [
                Duck(name="Quacker 1"),
                Duck(name="Debugger Buddy"),
                Duck(name="Syntax Squeaker"),
                Duck(name="Byte Bot"),
            ]
            db.session.add_all(members + ducks)
            db.session.commit()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
