# scene_manager.py

class SceneManager:
    def __init__(self, initial_scene):
        self.current_scene = initial_scene

    def switch(self, new_scene):
        self.current_scene = new_scene

    def handle_event(self, event):
        self.current_scene.handle_event(event)

    def update(self, dt):
        self.current_scene.update(dt)

    def render(self, screen):
        self.current_scene.render(screen)
