from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Transaction Monitoring System"
    database_url: str = "sqlite:///./transactions.db"
    debug: bool = True

    # Rate limiting for transaction submission, applied per account number.
    # capacity is the burst size; refill_rate is sustained submissions/second.
    rate_limit_enabled: bool = True
    rate_limit_capacity: float = 5
    rate_limit_refill_rate: float = 1.0

    class Config:
        env_file = ".env"


settings = Settings()
