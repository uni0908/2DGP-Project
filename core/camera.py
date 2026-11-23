"""플레이어를 따라가되 맵 끝을 벗어나지 않는 가로 카메라."""


class Camera:
    def __init__(self, view_width, world_width):
        self.view_width = view_width
        self.world_width = world_width
        self.x = 0.0

    def follow(self, target_x):
        self.x = max(0.0, min(target_x - self.view_width * 0.4,
                              max(0.0, self.world_width - self.view_width)))
