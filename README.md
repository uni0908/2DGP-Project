# Doodle Wars

pico2d로 개발하는 2D 액션 슈팅 게임입니다.

개발 요구사항과 단계별 완료 조건은 [PRD](docs/PRD.md)를 참고하세요.

## 기본 구조

- `main.py`: 게임 실행 시작점
- `play_mode.py`: 플레이 화면의 입력, 업데이트, 그리기
- `player.py`: 플레이어 이동, 점프, 총격
- `game_world.py`: 지형·플레이어의 레이어별 관리
- `doodle.py`: 고정 낙서 지형
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
- D: 바라보는 방향 앞에 낙서 생성 (공중에서도 가능, 화면 밖·겹치는 위치는 생성 불가)
- Escape 또는 창 닫기: 종료

현재 2단계까지 구현했습니다. 낙서는 아래에서 통과하고 위에 착지하며, 옆면은 막힙니다. 발판 위에서 이동·점프할 수 있고, 발판 밖으로 걸어 나가면 떨어집니다. 낙서 수량 소모·지우개·총격은 아직 구현하지 않았습니다. 임시 수치와 검증 결과는 PRD를 참고하세요.

충돌 회귀 테스트는 프로젝트 폴더에서 `..\.venv\Scripts\python.exe -m unittest discover -s tests -v`로 실행합니다.

수업 공용 환경은 상위 `2dgame/.venv`의 Python 3.13.7입니다. VS Code에서 `2dgame` 폴더를 열고 기존 `현재 수업 Python 파일 실행` 구성을 사용하거나, 프로젝트 폴더에서 `..\.venv\Scripts\python.exe main.py`로 실행할 수 있습니다.
