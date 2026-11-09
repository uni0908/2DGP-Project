"""플레이 객체와 고정 지형을 레이어별로 관리한다."""

TERRAIN = 0
ACTORS = 1
PROJECTILES = 2
_layers = [[], [], []]


def add_object(obj, layer):
    _layers[layer].append(obj)


def objects(layer):
    return tuple(_layers[layer])


def remove_object(obj):
    for layer in _layers:
        if obj in layer:
            layer.remove(obj)
            return


def clear():
    for layer in _layers:
        layer.clear()


def update(dt):
    for layer in _layers:
        for obj in tuple(layer):
            obj.update(dt)


def draw():
    for layer in _layers:
        for obj in layer:
            obj.draw()
