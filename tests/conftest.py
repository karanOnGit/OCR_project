import io
import os
import shutil
import tempfile
import pytest
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings, get_settings
from app.core.database import Base, get_db
from app.main import app
from app.api.deps import get_ocr_service_dep, get_google_docs_service_dep
from app.services.ocr_service import MockOCRService
from app.services.google_docs_service import MockGoogleDocsService


@pytest.fixture(scope="session")
def temp_dir():
    dir_path = tempfile.mkdtemp()
    yield dir_path
    shutil.rmtree(dir_path, ignore_errors=True)


@pytest.fixture
def test_settings(temp_dir):
    test_upload_dir = os.path.join(temp_dir, "uploads")
    os.makedirs(test_upload_dir, exist_ok=True)
    return Settings(
        APP_ENV="test",
        DEBUG=True,
        UPLOAD_DIR=test_upload_dir,
        MAX_FILE_SIZE_MB=2,
        DATABASE_URL=f"sqlite:///{temp_dir}/test_jobs.db",
        OCR_ENGINE="mock",
    )


@pytest.fixture
def db_session(test_settings):
    engine = create_engine(
        test_settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_ocr():
    return MockOCRService()


@pytest.fixture
def mock_google_docs():
    return MockGoogleDocsService()


@pytest.fixture
def client(db_session, test_settings, mock_ocr, mock_google_docs):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_get_settings():
        return test_settings

    def override_get_ocr():
        return mock_ocr

    def override_get_google_docs():
        return mock_google_docs

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings] = override_get_settings
    app.dependency_overrides[get_ocr_service_dep] = override_get_ocr
    app.dependency_overrides[get_google_docs_service_dep] = override_get_google_docs

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_image_bytes():
    """Generates a small valid PNG image with text."""
    image = Image.new("RGB", (200, 100), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.text((10, 40), "TEST OCR TEXT", fill=(0, 0, 0))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()
