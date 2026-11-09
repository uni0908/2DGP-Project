# Doodle Wars

pico2d로 개발하는 2D 액션 슈팅 게임입니다.

개발 요구사항과 단계별 완료 조건은 [PRD](docs/PRD.md)를 참고하세요.

## 기본 구조

- `main.py`: 게임 실행 시작점
- `play_mode.py`: 플레이 화면의 입력, 업데이트, 그리기
- `player.py`: 플레이어 이동, 점프, 총격
- `assets/images/`: 게임에서 사용하는 이미지
- `assets/sounds/`: 효과음과 배경음악
- `Slides/`: 기획서와 발표 자료

## 실행과 조작

Python과 pico2d가 설치된 환경에서 프로젝트 폴더를 열고 실행합니다.

```sh
python -m pip install pico2d
python main.py
```

- 왼쪽·오른쪽 방향키: 이동
- 스페이스바: 점프 (착지 후 다시 누르기)
- Escape 또는 창 닫기: 종료

현재 1단계인 창 실행, `Player` 클래스의 이동·점프·바닥 착지를 구현했습니다. 플레이어는 임시 사각형이며, 수치와 검증 결과는 PRD의 1단계 기록을 참고하세요.

수업 공용 환경은 상위 `2dgame/.venv`의 Python 3.13.7입니다. VS Code에서 `2dgame` 폴더를 열고 기존 `현재 수업 Python 파일 실행` 구성을 사용하거나, 프로젝트 폴더에서 `..\.venv\Scripts\python.exe main.py`로 실행할 수 있습니다.
