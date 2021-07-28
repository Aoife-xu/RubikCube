"""
only one sticker

"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import widgets
from projection import Quaternion, project_points

class Cube:

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

    def draw_interactive(self):
        fig = plt.figure(figsize=(5, 5))
        fig.add_axes(InteractiveCube(self))
        return fig

class InteractiveCube(plt.Axes):

    def __init__(self, cube=None,
                 fig=None, rect=[0.1, 0.16, 0.9, 0.84],
                 **kwargs): # **kwargs 多个参数，传入的参数是 dict 类型
        self.cube = cube
        if fig is None:
            fig = plt.gcf()# 获得当前图片

        # add some defaults, and draw axes
        kwargs.update(dict(xlim=kwargs.get('xlim', (-2.0, 2.0)),
                           ylim=kwargs.get('ylim', (-2.0, 2.0))))
        super(InteractiveCube, self).__init__(fig, rect, **kwargs)
        # Internal state variable
        self._draw_cube()

    def _draw_cube(self):
        stickers = self.cube.base_sticker[:, :2]
        print(stickers)
        sp = plt.Polygon(stickers)
        self.add_patch(sp)

if __name__ == '__main__':
    c = Cube()

    c.draw_interactive()

    plt.show()