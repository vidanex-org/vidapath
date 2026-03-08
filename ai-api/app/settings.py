from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    server_url: str
    internal_url_core: str
    public_key: str
    private_key: str
    project_name: str
    root_path: str
    pending_path: str
    ai_service_api_endpoint: str
    ai_service_secret_key: str

    @property
    def credential(self):
        return {
            "host": self.internal_url_core,
            "public_key": self.public_key,
            "private_key": self.private_key,
        }


settings = Settings()
