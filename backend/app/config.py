from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    APP_NAME: str = "BillMaster"
    DATABASE_URL: str = "postgresql://postgres:admin@127.0.0.1:5432/billing_db"
    DEFAULT_CURRENCY: str = "₹"
    COMPANY_NAME: str = "BillMaster Solutions"
    COMPANY_EMAIL: str = "billing@billmaster.io"
    COMPANY_PHONE: str = "+91 98765 43210"
    COMPANY_ADDRESS: str = "Tower B, Cyber City, Gurugram, Haryana 122002"
    COMPANY_TAX_ID: str = "07AAAAA0000A1Z5"
    INVOICE_PREFIX: str = "INV"
    DEFAULT_TAX_RATE: float = 18.0

settings = Settings()
