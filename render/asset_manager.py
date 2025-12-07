# [render/asset_manager.py] — tolerate missing folders & bad images, optional logging
import pygame, os

class AssetManager:
    def __init__(self):
        self.images = {}

    def load_folder(self, folder_path, scale=1.0, colorkey=None):
        if not os.path.isdir(folder_path):
            print(f"⚠ Assets folder missing: {folder_path}")
            return
        for filename in os.listdir(folder_path):
            if not filename.lower().endswith((".png", ".jpg", ".jpeg")):
                continue
            key = os.path.splitext(filename)[0]
            path = os.path.join(folder_path, filename)
            try:
                img = pygame.image.load(path).convert_alpha()
            except Exception as exc:
                print(f"⚠ Failed to load image '{path}': {exc}")
                continue
            if colorkey is not None:
                img.set_colorkey(colorkey)
            if scale != 1.0:
                img = pygame.transform.smoothscale(
                    img, (int(img.get_width()*scale), int(img.get_height()*scale))
                )
            self.images[key] = img

    def get(self, key):
        return self.images.get(key)
