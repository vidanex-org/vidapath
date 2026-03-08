from fastapi import APIRouter
from pydantic import BaseModel, Field

from pims import __version__
from pims.config import ReadableSettings, get_settings

router = APIRouter(prefix=get_settings().api_base_path)


class ServerInfo(BaseModel):
    version: str = Field(..., description="PIMS version")
    settings: ReadableSettings


class UIConfig(BaseModel):
    """UI configuration exposed to frontend."""
    easy_import_project_name_strategy: str = Field(
        ...,
        description="The strategy to determine project name for easy import ('folder', 'substring', 'pattern')"
    )


@router.get("/info", tags=["Server"])
async def show_status() -> ServerInfo:
    """
    PIMS Server status.
    """
    return ServerInfo(version=__version__, settings=get_settings())


@router.get("/ui-config", tags=["Server"])
async def get_ui_config() -> UIConfig:
    """
    Get UI configuration for frontend.
    """
    settings = get_settings()
    return UIConfig(
        easy_import_project_name_strategy=settings.easy_import_project_name_strategy
    )
