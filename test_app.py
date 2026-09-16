from datetime import timedelta

from app import app, db, DeluxeDuck, Duck, Loan, Member


def test_loan_is_created_with_due_date_seven_days_later():
    with app.app_context():
        db.drop_all()
        db.create_all()

        member = Member(name="Ada")
        duck = Duck(name="Quacker")
        db.session.add_all([member, duck])
        db.session.commit()

        loan = Loan.create(member_id=member.id, duck_id=duck.id)

        assert loan is not None
        assert loan.member_id == member.id
        assert loan.duck_id == duck.id
        assert loan.due_on - loan.borrowed_on == timedelta(days=7)
        assert duck.status == "on loan"


def test_deluxe_duck_loan_is_created_with_due_date_fourteen_days_later():
    with app.app_context():
        db.drop_all()
        db.create_all()

        member = Member(name="Ada")
        duck = DeluxeDuck(name="Deluxe Quacker", deposit=25.0)
        db.session.add_all([member, duck])
        db.session.commit()

        loan = Loan.create(member_id=member.id, duck_id=duck.id)

        assert loan is not None
        assert duck.deposit == 25.0
        assert loan.due_on - loan.borrowed_on == timedelta(days=14)


def test_member_can_have_multiple_active_loans():
    with app.app_context():
        db.drop_all()
        db.create_all()

        member = Member(name="Grace")
        duck1 = Duck(name="Duck 1")
        duck2 = Duck(name="Duck 2")
        db.session.add_all([member, duck1, duck2])
        db.session.commit()

        loan1 = Loan.create(member_id=member.id, duck_id=duck1.id)
        loan2 = Loan.create(member_id=member.id, duck_id=duck2.id)

        assert loan1 is not None
        assert loan2 is not None
        assert loan1.duck_id != loan2.duck_id
        assert member.active_loans_count() == 2


def test_duck_cannot_be_borrowed_if_already_on_loan():
    with app.app_context():
        db.drop_all()
        db.create_all()

        member1 = Member(name="Linus")
        member2 = Member(name="Margaret")
        duck = Duck(name="Debugger")
        db.session.add_all([member1, member2, duck])
        db.session.commit()

        Loan.create(member_id=member1.id, duck_id=duck.id)

        assert Loan.create(member_id=member2.id, duck_id=duck.id) is None
        assert duck.status == "on loan"
