from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Transaction Monitoring System"
    database_url: str = "sqlite:///./transactions.db"
    debug: bool = True
    
    class Config:
        env_file = ".env"


settings = Settings()
