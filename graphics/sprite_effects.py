"""원본 알파를 유지하는 런타임 피격 효과."""

import ctypes

import pico2d


def white_silhouette(image_path):
    original = pico2d.IMG_Load(str(image_path).encode('utf-8'))
    if not original:
        raise RuntimeError('피격 효과 원본 시트를 불러오지 못했습니다.')
    try:
        surface = pico2d.SDL_ConvertSurfaceFormat(original, pico2d.SDL_PIXELFORMAT_RGBA32, 0)
    finally:
        pico2d.SDL_FreeSurface(original)
    if not surface:
        raise RuntimeError('피격 효과 RGBA 변환에 실패했습니다.')
    try:
        size = surface.contents.pitch * surface.contents.h
        pixels = bytearray(ctypes.string_at(surface.contents.pixels, size))
        for channel in range(3):
            pixels[channel::4] = b'\xff' * (size // 4)
        ctypes.memmove(surface.contents.pixels, bytes(pixels), size)
        texture = pico2d.SDL_CreateTextureFromSurface(pico2d.load_image.__globals__['renderer'], surface)
        if not texture:
            raise RuntimeError('피격 효과 텍스처 생성에 실패했습니다.')
        return pico2d.Image(texture)
    finally:
        pico2d.SDL_FreeSurface(surface)
