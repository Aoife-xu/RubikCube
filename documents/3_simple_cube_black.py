"""
一个黑色立方体
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import widgets
from projection import Quaternion, project_points

class Cube:

    default_plastic_color = 'black'
    base_face = np.array([[1, 1, 1],  #
                          [1, -1, 1],
                          [-1, -1, 1],
                          [-1, 1, 1],
                          [1, 1, 1]], dtype=float)

    x, y, z = np.eye(3)
    rots = [Quaternion.from_v_theta(np.eye(3)[0], theta)
            for theta in (np.pi / 2, -np.pi / 2)]
    rots += [Quaternion.from_v_theta(np.eye(3)[1], theta)
             for theta in (np.pi / 2, -np.pi / 2, np.pi, 2 * np.pi)]

    def __init__(self):

        self.plastic_color = self.default_plastic_color
        self._initialize_arrays()

    def _initialize_arrays(self):
        translations = np.array([[[-1 + (i + 0.5) * 2/3,
                                   -1 + (j + 0.5) * 2/3, 0]]
                                 for i in range(3)
                                 for j in range(3)])
        faces = []
        factor = np.array([1. / 3, 1. / 3, 1])
        for i in range(6):
            M = self.rots[i].as_rotation_matrix()
            faces_t = np.dot(factor * self.base_face
                             + translations, M.T)
            faces.append(faces_t)

        self._faces = np.vstack(faces)


    def draw_interactive(self):
        fig = plt.figure(figsize=(5, 5))
        fig.add_axes(InteractiveCube(self))
        return fig

class InteractiveCube(plt.Axes):
    def __init__(self, cube=None,
                 interactive=True,
                 view=(0, 0, 10),
                 fig=None, rect=[0.1, 0.16, 0.9, 0.84],
                 **kwargs): # **kwargs 多个参数，传入的参数是 dict 类型
        self.cube = cube

        self._view = view
        self._start_rot = Quaternion.from_v_theta((1, -1, 0),
                                                  -np.pi / 6)
        if fig is None:
            fig = plt.gcf()# 获得当前图片

        # add some defaults, and draw axes
        kwargs.update(dict(xlim=kwargs.get('xlim', (-2.0, 2.0)),
                           ylim=kwargs.get('ylim', (-2.0, 2.0))))
        super(InteractiveCube, self).__init__(fig, rect, **kwargs)

        self._current_rot = self._start_rot


        self._draw_cube()

    def _project(self, pts):
        return project_points(pts, self._current_rot, self._view, [0, 1, 0])

    def _draw_cube(self):
        faces = self._project(self.cube._faces)[:, :, :2]

        plastic_color = self.cube.plastic_color

        for i in range(54):
            fp = plt.Polygon(faces[i], facecolor=plastic_color,)
            self.add_patch(fp)

if __name__ == '__main__':
    c = Cube()

    c.draw_interactive()

    plt.show()