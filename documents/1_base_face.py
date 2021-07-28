"""
1 only simple face 2*2

"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import widgets
from projection import Quaternion, project_points

class Cube:
    base_face = np.array([[1, 1, 1],  #
                          [1, -1, 1],
                          [-1, -1, 1],
                          [-1, 1, 1],
                          [1, 1, 1]], dtype=float)

    def draw_interactive(self):
        fig = plt.figure(figsize=(5, 5))
        fig.add_axes(InteractiveCube(self))
        return fig

class InteractiveCube(plt.Axes):
    def __init__(self, cube=None,
                 fig=None, rect=[0.1, 0.16, 0.9, 0.84],
                 **kwargs): # **kwargs 多个参数，传入的参数是 dict 类型
        if fig is None:
            fig = plt.gcf()# 获得当前图片

        # add some defaults, and draw axes
        kwargs.update(dict(xlim=kwargs.get('xlim', (-2.0, 2.0)),
                           ylim=kwargs.get('ylim', (-2.0, 2.0))))
        super(InteractiveCube, self).__init__(fig, rect, **kwargs)
        # Internal state variable
        self._draw_cube()

    def _draw_cube(self):

        fp = plt.Polygon([[1, 1],  #
                          [1, -1],
                          [-1, -1],
                          [-1, 1],
                          [1, 1]])
        self.add_patch(fp)

if __name__ == '__main__':
    c = Cube()

    c.draw_interactive()

    plt.show()