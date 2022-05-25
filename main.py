import pygame
import numpy as np
from engine import game, gameObject, colliders, activity, camera, colors, text



VERTEX_COLOR = colors.CYAN
EDGE_COLOR = colors.WHITE
WEIGHT_COLOR = colors.RED
SELECTED_COLOR = colors.GREEN
CONNECTED_COLOR = (0, 150, 40)

class SelectedVertex(gameObject.GameObject):
    def __init__(self):
        super().__init__(
            collider=colliders.Collider.CIRCLE,
            position=(0, 0),
            tag='selected'
        )
        self.connected = []
        self.lines = []
        self.index = -1
        self.changed = False

class Vertex(gameObject.GameObject):
    def __init__(self, position, num, radius=5):
        super().__init__(
            collider=colliders.Collider.CIRCLE,
            position=(0, 0),
            text=text.Text(str(num), font_name='monospace', font_color=colors.RED, font_percent_size=0.03),
            tag='vertex'
        )
        self.radius = radius
        self.base_position = position
        self.window_w, self.window_h = (0, 0)
        self.selected = None
        self.index = num

    def draw(self, window: pygame.Surface, cam: camera.Camera, get_gameobject_by_tag):
        if self.selected is None:
            self.selected = get_gameobject_by_tag('selected')

        self.window_w, self.window_h = window.get_size()

        self.radius = min(self.window_w , self.window_h) // 40

        self.position = (self.base_position[0] + self.window_w // 2, self.base_position[1] + self.window_h // 2)

        color = VERTEX_COLOR
        if self.selected.index == self.index:
            color = SELECTED_COLOR

        elif self.index in self.selected.connected:
            color = CONNECTED_COLOR

        pygame.draw.circle(window, color, self.position, self.radius)

        super().draw(window, cam, get_gameobject_by_tag)

    def on_click(self):
        if self.selected is not None:
            self.selected.index = self.index
            self.selected.changed = True


class GraphActivity(activity.BaseActivity):
    def __init__(self, graph_path):
        super().__init__(
            bg_color=(20, 20, 20)
        )

        self.radius = 0

        self.vertices = []
        self.edges = []

        self.min_weight = None
        self.max_weight = None

        self.selected = SelectedVertex()
        self.gameObjects.append(self.selected)

        with open(graph_path) as f:
            self.vertices_num, self.edges_num = [int(x) for x in f.readline().split(" ")]
            self.positions = []

            self.gamma = np.pi - ((self.vertices_num - 2) * np.pi / self.vertices_num)
            if self.gamma == 0:
                self.gamma = np.pi

            for _ in range(self.edges_num):
                start, end, weight = [int(x) for x in f.readline().split(" ")]

                if self.min_weight is None:
                    self.min_weight = weight
                    self.max_weight = weight

                self.min_weight = min(self.min_weight, weight)
                self.max_weight = max(self.max_weight, weight)

                self.edges.append((weight, start, end))

            for i in range(self.vertices_num):
                v = Vertex((0, 0), i + 1)
                self.positions.append((0, 0))
                self.gameObjects.append(v)
                self.vertices.append(v)

            self.update_vertices()

    def transform(self, min_val, max_val, val):
        return (val - self.min_weight) *  (max_val - min_val) / (self.max_weight - self.min_weight) + min_val

    def update_vertices(self):
        cur_x = self.radius if self.vertices_num > 0 else 0
        cur_y = 0
        angle = 0

        i = 0
        for g in self.gameObjects:
            if g.tag == 'vertex':
                g.base_position = (cur_x, cur_y)

                angle += self.gamma
                cur_x = self.radius * np.cos(angle)
                cur_y = self.radius * np.sin(angle)

                i += 1


    def on_resize(self, size):
        self.radius = min(size[0] // 3, size[1] // 3)
        self.update_vertices()

    def pre_update(self, g, session: dict):
        if self.selected.changed:
            self.selected.connected.clear()
            self.selected.lines.clear()

        for i, v in enumerate(self.vertices):
            self.positions[i] = v.position

        for w, s, e in self.edges:
            pos_s = self.positions[s - 1]
            pos_e = self.positions[e - 1]

            if s == self.selected.index or e == self.selected.index:
                if self.selected.changed:
                    self.selected.connected.append(s)
                    self.selected.connected.append(e)
                    self.selected.lines.append((w, s, e))
                continue

            t = self.transform(2, 10, w)
            pygame.draw.line(g.window, EDGE_COLOR, pos_s, pos_e, width=int(t))

        for w, s, e in self.selected.lines:
            pos_s = self.positions[s - 1]
            pos_e = self.positions[e - 1]
            t = self.transform(2, 10, w)
            pygame.draw.line(g.window, CONNECTED_COLOR, pos_s, pos_e, width=int(t))

        if self.selected.changed:
            self.selected.changed = False


class GraphVisualizer(game.Game):
    def __init__(self, graph_path):
        super().__init__(resizable=True)
        self.activities = {
            'main': GraphActivity(graph_path)
        }

        self.fps_target = 20

        self.current_activity = self.activities['main']
        self.current_activity.start(self.session)
        self.current_activity.on_resize(self.window.get_size())


def main():
    gh = GraphVisualizer('graf.txt')
    gh.run_loop()

if __name__ == '__main__':
    main()
