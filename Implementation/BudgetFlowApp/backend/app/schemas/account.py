from datetime import datetime
from decimal import Decimal
from typing import Optional, Literal, Union, Annotated
import uuid

from pydantic import BaseModel, Field, ConfigDict


class InstitutionRead(BaseModel):
    id: uuid.UUID
    name: str
    model_config = ConfigDict(from_attributes=True)


class AccountCreateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    institution_id: Optional[uuid.UUID] = None
    currency: str = Field(default="USD", min_length=3, max_length=3)
    balance: Optional[Decimal] = Field(default=0, ge=0)


class BankAccountCreate(AccountCreateBase):
    type: Literal["bank"] = "bank"
    bank_account_number_last4: Optional[str] = Field(None, min_length=4, max_length=4)


class CreditCardAccountCreate(AccountCreateBase):
    type: Literal["credit"] = "credit"
    credit_card_last4: Optional[str] = Field(None, min_length=4, max_length=4)
    credit_limit: Optional[float] = Field(None, ge=0)


class InvestmentAccountCreate(AccountCreateBase):
    type: Literal["investment"] = "investment"
    broker_name: Optional[str] = None


AccountCreate = Annotated[
    Union[BankAccountCreate, CreditCardAccountCreate, InvestmentAccountCreate],
    Field(discriminator="type"),
]


class AccountUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    institution_id: Optional[uuid.UUID] = None
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    balance: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None
    bank_account_number_last4: Optional[str] = Field(None, min_length=4, max_length=4)
    credit_card_last4: Optional[str] = Field(None, min_length=4, max_length=4)
    credit_limit: Optional[float] = Field(None, ge=0)
    broker_name: Optional[str] = None


class AccountRead(BaseModel):
    id: uuid.UUID
    type: str
    name: str
    currency: str
    balance: Decimal
    is_active: bool
    institution_id: Optional[uuid.UUID] = None
    institution: Optional[InstitutionRead] = None
    bank_account_number_last4: Optional[str] = None
    credit_card_last4: Optional[str] = None
    credit_limit: Optional[float] = None
    broker_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
