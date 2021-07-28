"""
simple stickers with colors
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import widgets
from projection import Quaternion, project_points

class Cube:

    default_face_colors = ["gray", "yellow",  # white, blue, yellow green, orange, red
                           "blue", "green",
                           "orange", "red",
                           "gray", "none"]

    stickerwidth = 0.9
    stickermargin = 0.5 * (1. - stickerwidth)
    stickerthickness = 0.001
    (d1, d2, d3) = (1 - stickermargin,
                    1 - 2 * stickermargin,
                    1 + stickerthickness)
    base_sticker = np.array([[d1, d2, d3], [d2, d1, d3],
                             [-d2, d1, d3], [-d1, d2, d3],
                             [-d1, -d2, d3], [-d2, -d1, d3],
                             [d2, -d1, d3], [d1, -d2, d3],
                             [d1, d2, d3]], dtype=float)
    base_face_centroid = np.array([[0, 0, 1]])

    x, y, z = np.eye(3)
    rots = [Quaternion.from_v_theta(np.eye(3)[0], theta)
            for theta in (np.pi / 2, -np.pi / 2)]
    rots += [Quaternion.from_v_theta(np.eye(3)[1], theta)
             for theta in (np.pi / 2, -np.pi / 2, np.pi, 2 * np.pi)]

    def __init__(self):


        self.face_colors = self.default_face_colors
        self._initialize_arrays()

    def _initialize_arrays(self):
        translations = np.array([[[-1 + (i + 0.5) * 2/3,
                                   -1 + (j + 0.5) * 2/3, 0]]
                                 for i in range(3)
                                 for j in range(3)])

        stickers = []
        colors = []

        factor = np.array([1. / 3, 1. / 3, 1])
        for i in range(6):
            M = self.rots[i].as_rotation_matrix()
            stickers_t = np.dot(factor * self.base_sticker
                                + translations, M.T)
            face_centroids_t = np.dot(self.base_face_centroid
                                      + translations, M.T)
            colors_i = i + np.zeros(face_centroids_t.shape[0], dtype=int)

            stickers.append(stickers_t)
            colors.append(colors_i)

        self._stickers = np.vstack(stickers)
        self._colors = np.concatenate(colors)

    def draw_interactive(self):
        fig = plt.figure(figsize=(5, 5))
        fig.add_axes(InteractiveCube(self))
        return fig

class InteractiveCube(plt.Axes):

    def __init__(self, cube=None,
                 interactive=True,
                 view=(0, 0, 10),
                 fig=None, rect=[0.1, 0.16, 0.9, 0.84],
                 **kwargs):  # **kwargs 多个参数，传入的参数是 dict 类型
        self.cube = cube

        self._view = view
        self._start_rot = Quaternion.from_v_theta((1, -1, 0),
                                                  -np.pi / 6)
        if fig is None:
            fig = plt.gcf()  # 获得当前图片

        # add some defaults, and draw axes
        kwargs.update(dict(xlim=kwargs.get('xlim', (-2.0, 2.0)),
                           ylim=kwargs.get('ylim', (-2.0, 2.0))))
        super(InteractiveCube, self).__init__(fig, rect, **kwargs)

        self._current_rot = self._start_rot

        self._draw_cube()

    def _project(self, pts):
        return project_points(pts, self._current_rot, self._view, [0, 1, 0])

    def _draw_cube(self):
        stickers = self._project(self.cube._stickers)[:, :, :2]

        colors = np.array(["gray", "yellow",
                           "blue", "green",
                           "orange", "red",
                           "gray", "none"])[self.cube._colors]

        for i in range(54):
            sp = plt.Polygon(stickers[i], facecolor=colors[i])
            self.add_patch(sp)

if __name__ == '__main__':
    c = Cube()

    c.draw_interactive()

    plt.show()