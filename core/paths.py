"""실행 위치나 모듈 폴더와 관계없는 프로젝트 경로."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
