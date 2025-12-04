from fastapi import FastAPI, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .database import Base, engine, SessionLocal
from . import models, schemas, utils


Base.metadata.create_all(bind=engine)

app = FastAPI(title="SmartPay - Simple Payment Gateway (MySQL)")

templates = Jinja2Templates(directory="templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@app.post("/merchants/signup")
def merchant_signup(
    payload: schemas.MerchantCreate,
    db: Session = Depends(get_db),
):

    existing = (
        db.query(models.Merchant)
        .filter(models.Merchant.email == payload.email)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Merchant already exists")
    api_key = utils.generate_api_key()

   
    merchant = models.Merchant(
        name=payload.name,
        email=payload.email,
        password=payload.password,  
        api_key=api_key,
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)

    return {
        "message": "Merchant registered",
        "merchant_id": merchant.id,
        "api_key": merchant.api_key,
    }


@app.post("/merchants/login")
def merchant_login(
    payload: schemas.MerchantLogin,
    db: Session = Depends(get_db),
):
    merchant = (
        db.query(models.Merchant)
        .filter(
            models.Merchant.email == payload.email,
            models.Merchant.password == payload.password,
        )
        .first()
    )

    if not merchant:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "message": "Login success",
        "merchant_id": merchant.id,
        "api_key": merchant.api_key,
    }


@app.post("/orders", response_model=schemas.OrderOut)
def create_order(
    payload: schemas.OrderCreate,
    db: Session = Depends(get_db),
):
    merchant = utils.get_merchant_by_api_key(db, payload.merchant_api_key)
    if not merchant:
        raise HTTPException(status_code=401, detail="Invalid API key")

    order = models.Order(
        merchant_id=merchant.id,
        amount=payload.amount,
        currency=payload.currency,
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    return order


@app.get("/pay/{order_id}", response_class=HTMLResponse)
def pay_page(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        return HTMLResponse("Invalid order", status_code=404)

    merchant = (
        db.query(models.Merchant)
        .filter(models.Merchant.id == order.merchant_id)
        .first()
    )

    return templates.TemplateResponse(
        "payment_page.html",
        {
            "request": request,
            "order_id": order.id,
            "amount": order.amount,
            "currency": order.currency,
            "merchant_name": merchant.name if merchant else "Unknown",
        },
    )


@app.post("/payments/confirm")
def confirm_payment(
    order_id: int = Form(...),
    mode: str = Form("CARD"),
    result: str = Form(...),  # "SUCCESS" or "FAILED"
    db: Session = Depends(get_db),
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        return HTMLResponse("Invalid order", status_code=404)

    payment = models.Payment(
        order_id=order.id,
        mode=mode,
        status="SUCCESS" if result == "SUCCESS" else "FAILED",
        txn_ref=f"TXN-{order.id}",
    )
    db.add(payment)

    if result == "SUCCESS":
        order.status = "PAID"
    else:
        order.status = "FAILED"

    db.commit()

    return RedirectResponse(
        url=f"/dashboard/{order.merchant_id}",
        status_code=302,
    )

@app.get("/dashboard/{merchant_id}", response_class=HTMLResponse)
def dashboard(
    merchant_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    merchant = (
        db.query(models.Merchant)
        .filter(models.Merchant.id == merchant_id)
        .first()
    )
    if not merchant:
        return HTMLResponse("Merchant not found", status_code=404)

    orders = (
        db.query(models.Order)
        .filter(models.Order.merchant_id == merchant_id)
        .order_by(models.Order.id.desc())
        .all()
    )

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "merchant": merchant,
            "orders": orders,
        },
    )
