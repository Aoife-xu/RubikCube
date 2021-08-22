import numpy as np
import matplotlib.pyplot as plt
import random
from matplotlib import widgets
from projection import Quaternion, project_points

from data import Cube
from flower_rotate import Rotate_s

def draw_interactive(self):
    fig = plt.figure(figsize=(5, 5))
    fig.add_axes(InteractiveCube(self))
    return fig

class InteractiveCube(plt.Axes):
    def __init__(self, cube=None,
                 interactive=True,
                 view=(0, 0, 10),
                 fig=None, rect=[0, 0.16, 1, 0.84],
                 **kwargs):
        if cube is None:
            self.cube = Cube(3)
        elif isinstance(cube, Cube):
            self.cube = cube
        else:
            self.cube = Cube(cube)

        self._view = view
        self._start_rot = Quaternion.from_v_theta((1, -1, 0),
                                                 -np.pi / 6)
        self.white_cross_List = [1, 3, 5, 7]
        self.s_new = []
        self.s = [*range(54)]
        if fig is None:
            fig = plt.gcf()

        # disable default key press events
        callbacks = fig.canvas.callbacks.callbacks
        del callbacks['key_press_event']

        # add some defaults, and draw axes
        kwargs.update(dict(aspect=kwargs.get('aspect', 'equal'),
                           xlim=kwargs.get('xlim', (-4.0, 4.0)),
                           ylim=kwargs.get('ylim', (-4.0, 4.0)),
                           frameon=kwargs.get('frameon', False),
                           xticks=kwargs.get('xticks', []),
                           yticks=kwargs.get('yticks', [])))
        super(InteractiveCube, self).__init__(fig, rect, **kwargs)
        self.xaxis.set_major_formatter(plt.NullFormatter())
        self.yaxis.set_major_formatter(plt.NullFormatter())

        self._start_xlim = kwargs['xlim']
        self._start_ylim = kwargs['ylim']

        # Define movement for up/down arrows or up/down mouse movement
        self._ax_UD = (1, 0, 0)
        self._step_UD = 0.01

        # Define movement for left/right arrows or left/right mouse movement
        self._ax_LR = (0, -1, 0)
        self._step_LR = 0.01

        self._ax_LR_alt = (0, 0, 1)

        # Internal state variable
        self._active = False  # true when mouse is over axes
        self._button1 = False  # true when button 1 is pressed
        self._button2 = False  # true when button 2 is pressed
        self._event_xy = None  # store xy position of mouse event
        self._shift = False  # shift key pressed
        self._digit_flags = np.zeros(10, dtype=bool)  # digits 0-9 pressed

        self._current_rot = self._start_rot  # current rotation state
        self._face_polys = None
        self._sticker_polys = None

        self._draw_cube()

        # connect some GUI events
        self.figure.canvas.mpl_connect('button_press_event',
                                       self._mouse_press)
        self.figure.canvas.mpl_connect('button_release_event',
                                       self._mouse_release)
        self.figure.canvas.mpl_connect('motion_notify_event',
                                       self._mouse_motion)
        self.figure.canvas.mpl_connect('key_press_event',
                                       self._key_press)
        self.figure.canvas.mpl_connect('key_release_event',
                                       self._key_release)

        self._initialize_widgets()

        # write some instructions
        self.figure.text(0.05, 0.9,
                         "U/D/L/R/B/F keys turn faces\n",
                         size=8)

    def _initialize_widgets(self):
        self._ax_scramble = self.figure.add_axes([0.35, 0.05, 0.2, 0.075])
        self._btn_scramble = widgets.Button(self._ax_scramble, 'Scramble')
        self._btn_scramble.on_clicked(self._scramble_cube)

        self._ax_reset = self.figure.add_axes([0.75, 0.05, 0.2, 0.075])
        self._btn_reset = widgets.Button(self._ax_reset, 'Reset View')
        self._btn_reset.on_clicked(self._reset_view)

        self._ax_solve = self.figure.add_axes([0.55, 0.05, 0.2, 0.075])
        self._btn_solve = widgets.Button(self._ax_solve, 'Solve Cube')
        self._btn_solve.on_clicked(self._solve_cube)

    def _project(self, pts):
        return project_points(pts, self._current_rot, self._view, [0, 1, 0])

    def _draw_cube(self):
        stickers = self._project(self.cube._stickers)[:, :, :2]
        faces = self._project(self.cube._faces)[:, :, :2]
        face_centroids = self._project(self.cube._face_centroids[:, :3])
        sticker_centroids = self._project(self.cube._sticker_centroids[:, :3])

        plastic_color = self.cube.plastic_color
        colors = np.asarray(self.cube.face_colors)[self.cube._colors]

        face_zorders = -face_centroids[:, 2]
        sticker_zorders = -sticker_centroids[:, 2]

        if self._face_polys is None:
            # initial call: create polygon objects and add to axes
            self._face_polys = []
            self._sticker_polys = []

            for i in range(len(colors)):
                fp = plt.Polygon(faces[i], facecolor=plastic_color,
                                 zorder=face_zorders[i])
                sp = plt.Polygon(stickers[i], facecolor=colors[i],
                                 zorder=sticker_zorders[i])

                self._face_polys.append(fp)
                self._sticker_polys.append(sp)
                self.add_patch(fp)  # 空心
                self.add_patch(sp)  # 全黑，add_path将图形添加到图里
        else:
            # subsequent call: update the polygon objects
           for i in range(len(colors)):
                self._face_polys[i].set_xy(faces[i])
                self._face_polys[i].set_zorder(face_zorders[i])
                self._face_polys[i].set_facecolor(plastic_color)

                self._sticker_polys[i].set_xy(stickers[i])
                self._sticker_polys[i].set_zorder(sticker_zorders[i])
                self._sticker_polys[i].set_facecolor(colors[i])

        self.figure.canvas.draw()

    def rotate(self, rot):
        self._current_rot = self._current_rot * rot

    def rotate_face(self, f, turns=1, layer=0, steps=1):
        if not np.allclose(turns, 0):

         self.cube.rotate_face(f)

         self._draw_cube()



    def _reset_view(self, *args):
        self.set_xlim(self._start_xlim)
        self.set_ylim(self._start_ylim)
        self._current_rot = self._start_rot
        self._draw_cube()


    def _key_press(self, event):
        """Handler for key press events"""
        if event.key == 'shift':
            self._shift = True
        elif event.key.isdigit():
            self._digit_flags[int(event.key)] = 1

        elif event.key == 'right':
            if self._shift:
                ax_LR = self._ax_LR_alt
            else:
                ax_LR = self._ax_LR
            self.rotate(Quaternion.from_v_theta(ax_LR,
                                                5 * self._step_LR))

        elif event.key == 'left':
            if self._shift:
                ax_LR = self._ax_LR_alt
            else:
                ax_LR = self._ax_LR
            self.rotate(Quaternion.from_v_theta(ax_LR,
                                                -5 * self._step_LR))
        elif event.key == 'up':
            self.rotate(Quaternion.from_v_theta(self._ax_UD,
                                                5 * self._step_UD))
        elif event.key == 'down':
            self.rotate(Quaternion.from_v_theta(self._ax_UD,
                                                -5 * self._step_UD))
        elif event.key.upper() in 'LRUDBF':
            if self._shift:
                direction = -1
            else:
                direction = 1

            if np.any(self._digit_flags[:N]):
                for d in np.arange(N)[self._digit_flags[:N]]:
                    self.rotate_face(event.key.upper(), direction, layer=d)

            else:
                self.rotate_face(event.key.upper(), direction)

        self._draw_cube()

    def _key_release(self, event):
        """Handler for key release event"""
        if event.key == 'shift':
            self._shift = False
        elif event.key.isdigit():
            self._digit_flags[int(event.key)] = 0

    def _mouse_press(self, event):
        """Handler for mouse button press"""
        self._event_xy = (event.x, event.y)
        if event.button == 1:
            self._button1 = True
        elif event.button == 3:
            self._button2 = True

    def _mouse_release(self, event):
        """Handler for mouse button release"""
        self._event_xy = None
        if event.button == 1:
            self._button1 = False
        elif event.button == 3:
            self._button2 = False

    def _mouse_motion(self, event):
        """Handler for mouse motion"""
        if self._button1 or self._button2:
            dx = event.x - self._event_xy[0]
            dy = event.y - self._event_xy[1]
            self._event_xy = (event.x, event.y)

            if self._button1:
                if self._shift:
                    ax_LR = self._ax_LR_alt
                else:
                    ax_LR = self._ax_LR
                rot1 = Quaternion.from_v_theta(self._ax_UD,
                                               self._step_UD * dy)
                rot2 = Quaternion.from_v_theta(ax_LR,
                                               self._step_LR * dx)
                self.rotate(rot1 * rot2)

                self._draw_cube()

            if self._button2:
                factor = 1 - 0.003 * (dx + dy)
                xlim = self.get_xlim()
                ylim = self.get_ylim()
                self.set_xlim(factor * xlim[0], factor * xlim[1])
                self.set_ylim(factor * ylim[0], factor * ylim[1])

                self.figure.canvas.draw()

    def _scramble_cube(self, *args):
        face = ['U', 'D', 'F', 'B', 'L', 'R']
        self.sequence = [*range(50)]
        for i in range(50):
            s = random.choice(face)
            self.sequence[i] = s
            self.cube.rotate_face(s)

        self.s = Rotate_s(self.sequence, self.s)
        print('s')
        print(self.sequence)
        print("scamble sequence:", self.s)
        print('scramble w', self.search_white(self.s))
        self._draw_cube()

        return self.sequence

    def white_cross(self):
        move = []

        while any(self.s[i] > 9 for i in [10, 14, 16, 12]):
            # l
            self.w = self.search_white(self.s)
            while any(self.s[i] < 8 for i in [19, 28, 46, 37]):
                print(self.s)
                w = self.search_white(self.s)
                self.wise_clock(w, [46, 28, 37, 19], {19, 37}, move)

            # l2
            self.w = self.search_white(self.s)
            while any(self.s[i] < 8 for i in [5, 1, 3, 7]):
                w = self.search_white(self.s)
                self.clock(w, [5, 1, 3, 7], {1, 5}, move)

            self.w = self.search_white(self.s)
            while any(self.s[i] < 8 for i in [19, 28, 46, 37]):
                print(self.s)
                w = self.search_white(self.s)
                self.wise_clock(w, [46, 28, 37, 19], {19, 37}, move)

            # l3
            self.w = self.search_white(self.s)
            while any(self.s[i] < 8 for i in [25, 43, 34, 52]):
                w = self.search_white(self.s)
                self.edge_r(self.w, [25, 43, 34, 52], {25, 34}, ['F', 'L', 'B', 'R'], [14, 10, 12, 16], move)

            self.w = self.search_white(self.s)
            while any(self.s[i] < 8 for i in [5, 1, 3, 7]):
                w = self.search_white(self.s)
                self.clock(w, [5, 1, 3, 7], {1, 5}, move)

            self.w = self.search_white(self.s)
            while any(self.s[i] < 8 for i in [19, 28, 46, 37]):
                w = self.search_white(self.s)
                self.wise_clock(w, [46, 28, 37, 19], {19, 37}, move)

            #l 到第一步
            self.w = self.search_white(self.s)
            while any(self.s[i] < 8 for i in [21, 48, 30, 39]):
                w = self.search_white(self.s)
                self.wise_clock(w, [21, 48, 30, 39], {21, 39}, move)
                self.w = self.search_white(self.s)
                self.wise_clock(w, [46, 28, 37, 19], {19, 37}, move)

            self.w = self.search_white(self.s)
            while any(self.s[i] < 8 for i in [25, 43, 34, 52]):
                w = self.search_white(self.s)
                self.edge_r(self.w, [25, 43, 34, 52], {25, 34}, ['F', 'L', 'B', 'R'], [14, 10, 12, 16], move)

            self.w = self.search_white(self.s)
            while any(self.s[i] < 8 for i in [5, 1, 3, 7]):
                w = self.search_white(self.s)
                self.clock(w, [5, 1, 3, 7], {1, 5}, move)

            self.w = self.search_white(self.s)
            while any(self.s[i] < 8 for i in [19, 28, 46, 37]):
                w = self.search_white(self.s)
                self.wise_clock(w, [46, 28, 37, 19], {19, 37}, move)

            # 转到l3
            self.w = self.search_white(self.s)
            while any(self.s[i] < 8 for i in [32, 23, 50, 41]):
                w = self.search_white(self.s)
                self.wise_clock(w, [23, 50, 32, 41], {23, 41}, move)
                self.w = self.search_white(self.s)
                self.edge_r(self.w, [25, 43, 34, 52], {25, 34}, ['F', 'L', 'B', 'R'], [14, 10, 12, 16], move)

            self.w = self.search_white(self.s)
            while any(self.s[i] < 8 for i in [21, 48, 30, 39]):
                w = self.search_white(self.s)
                self.wise_clock(w, [21, 48, 30, 39], {21, 39}, move)
                self.w = self.search_white(self.s)
                self.wise_clock(w, [46, 28, 37, 19], {19, 37}, move)

            self.w = self.search_white(self.s)
            while any(self.s[i] < 8 for i in [25, 43, 34, 52]):
                w = self.search_white(self.s)
                self.edge_r(self.w, [25, 43, 34, 52], {25, 34}, ['F', 'L', 'B', 'R'], [14, 10, 12, 16], move)

            self.w = self.search_white(self.s)
            while any(self.s[i] < 8 for i in [5, 1, 3, 7]):
                w = self.search_white(self.s)
                self.clock(w, [5, 1, 3, 7], {1, 5}, move)

            self.w = self.search_white(self.s)
            while any(self.s[i] < 8 for i in [19, 28, 46, 37]):
                w = self.search_white(self.s)
                self.wise_clock(w, [46, 28, 37, 19], {19, 37}, move)

        print('flower move:', move)

    def wise_clock(self,  w, edge_white, anti_step, move):
        self.edge_w( w, edge_white, anti_step, ['L', 'F', 'R', 'B'], [10, 14, 16, 12], move)

    def clock(self, w, edge_white, anti_step, move):
        self.top(w, edge_white, anti_step, ['F', 'L', 'B', 'R'], [14, 10, 12, 16], move)

    def edge_w(self, w, edge_white, anti_step, move_step, down, move): # 找到4白色放到某四个位置

        if any(w[i] in edge_white for i in range(4)):  # 侧边是否有白色

            if anti_step.issubset(set(w)):
                if any(w[i] == edge_white[0] for i in range(4)):
                    self.pattern_1(move_step[0], down[0], self.s, move)

                if any(w[i] == edge_white[1] for i in range(4)):
                    self.pattern_1(move_step[1], down[1], self.s, move)

                if any(w[i] == edge_white[2] for i in range(4)):
                    self.pattern_1(move_step[2], down[2], self.s, move)

                if any(w[i] == edge_white[3] for i in range(4)):
                    self.pattern_1(move_step[3], down[3], self.s, move)

            else:
                if any(w[i] == edge_white[3] for i in range(4)):
                    self.pattern_1(move_step[3], down[3], self.s, move)
                if any(w[i] == edge_white[0] for i in range(4)):
                    self.pattern_1(move_step[0], down[0], self.s, move)
                if any(w[i] == edge_white[1] for i in range(4)):
                    self.pattern_1(move_step[1], down[1], self.s, move)
                if any(w[i] == edge_white[2] for i in range(4)):
                    self.pattern_1(move_step[2], down[2], self.s, move)
        else:
            print("no white edges")
        print("move:", move)

    def top(self, w, edge_white, anti_step, move_step, down, move): # 找到4白色放到某四个位置

        if any(w[i] in edge_white for i in range(4)):  # edge_white 是否白色

            if anti_step.issubset(set(w)):
                if any(w[i] == edge_white[0] for i in range(4)):
                    self.pattern_1(move_step[0], down[0], self.s, move)
                    self.pattern_1(move_step[0], down[0], self.s, move)

                if any(w[i] == edge_white[1] for i in range(4)):
                    self.pattern_1(move_step[1], down[1], self.s, move)
                    self.pattern_1(move_step[1], down[1], self.s, move)

                if any(w[i] == edge_white[2] for i in range(4)):
                    self.pattern_1(move_step[2], down[2], self.s, move)
                    self.pattern_1(move_step[2], down[2], self.s, move)

                if any(w[i] == edge_white[3] for i in range(4)):
                    self.pattern_1(move_step[3], down[3], self.s, move)
                    self.pattern_1(move_step[3], down[3], self.s, move)

            else:
                if any(w[i] == edge_white[3] for i in range(4)):
                    self.pattern_1(move_step[3], down[3], self.s, move)
                    self.pattern_1(move_step[3], down[3], self.s, move)

                if any(w[i] == edge_white[0] for i in range(4)):
                    self.pattern_1(move_step[0], down[0], self.s, move)
                    self.pattern_1(move_step[0], down[0], self.s, move)

                if any(w[i] == edge_white[1] for i in range(4)):
                    self.pattern_1(move_step[1], down[1], self.s, move)
                    self.pattern_1(move_step[1], down[1], self.s, move)

                if any(w[i] == edge_white[2] for i in range(4)):
                    self.pattern_1(move_step[2], down[2], self.s, move)
                    self.pattern_1(move_step[2], down[2], self.s, move)
        else:
            print("no white edges")
        print("move:", move)

    def edge_r(self, w, edge_white, anti_step, move_step, down, move): # 找到4白色放到某四个位置

        if any(w[i] in edge_white for i in range(4)):  # edge_white 是否白色

            if anti_step.issubset(set(w)):
                if any(w[i] == edge_white[0] for i in range(4)):
                    self.pattern_1(move_step[0], down[0], self.s, move)
                    self.pattern_1(move_step[0], down[0], self.s, move)
                    self.pattern_1(move_step[0], down[0], self.s, move)

                if any(w[i] == edge_white[1] for i in range(4)):
                    self.pattern_1(move_step[1], down[1], self.s, move)
                    self.pattern_1(move_step[1], down[1], self.s, move)
                    self.pattern_1(move_step[1], down[1], self.s, move)


                if any(w[i] == edge_white[2] for i in range(4)):
                    self.pattern_1(move_step[2], down[2], self.s, move)
                    self.pattern_1(move_step[2], down[2], self.s, move)
                    self.pattern_1(move_step[2], down[2], self.s, move)

                if any(w[i] == edge_white[3] for i in range(4)):
                    self.pattern_1(move_step[3], down[3], self.s, move)
                    self.pattern_1(move_step[3], down[3], self.s, move)
                    self.pattern_1(move_step[3], down[3], self.s, move)

            else:
                if any(w[i] == edge_white[3] for i in range(4)):
                    self.pattern_1(move_step[3], down[3], self.s, move)
                    self.pattern_1(move_step[3], down[3], self.s, move)
                    self.pattern_1(move_step[3], down[3], self.s, move)

                if any(w[i] == edge_white[0] for i in range(4)):
                    self.pattern_1(move_step[0], down[0], self.s, move)
                    self.pattern_1(move_step[0], down[0], self.s, move)
                    self.pattern_1(move_step[0], down[0], self.s, move)

                if any(w[i] == edge_white[1] for i in range(4)):
                    self.pattern_1(move_step[1], down[1], self.s, move)
                    self.pattern_1(move_step[1], down[1], self.s, move)
                    self.pattern_1(move_step[1], down[1], self.s, move)

                if any(w[i] == edge_white[2] for i in range(4)):
                    self.pattern_1(move_step[2], down[2], self.s, move)
                    self.pattern_1(move_step[2], down[2], self.s, move)
                    self.pattern_1(move_step[2], down[2], self.s, move)
        else:
            print("no white edges")
        print("edge_r move:", move)

    """
    move传递不过去
    def edge_d(self, w, move):  # 找到4白色放到某四个位置
        self.wise_clock(w, [21, 48, 30, 39], {21, 39}, move)
        self.w = self.search_white(self.s)
        self.wise_clock(w, [46, 28, 37, 19], {19, 37}, move)
    """

    def pattern_1(self, f, d, s, move): # single rotation lfrb

        if not s[d] in self.white_cross_List:
            self.rotate_face(f)
            self.s = Rotate_s(f, s)
            print("rotate sequence:", self.s)
            move.append(f)
        else:
            while s[d] in self.white_cross_List:
                self.rotate_face('D', s)
                self.s = Rotate_s('D', s)
                move.append('D')

            self.rotate_face(f)
            self.s = Rotate_s(f, s)
            move.append(f)

    def search_white(self, s):
        w = []
        for i in range(53):
            if s[i] in self.white_cross_List:
                w.append(i)
        print("search:", w)
        return w

    def _solve_cube(self, *args):

        self.white_cross()
        self._draw_cube()



if __name__ == '__main__':
    import sys

    try:
        N = int(sys.argv[1])
    except:
        N = 3

    c = Cube()

    # do a 3-corner swap
    # c.rotate_face('R')
    # c.rotate_face('D')
    # c.rotate_face('R', -1)
    # c.rotate_face('U', -1)
    # c.rotate_face('R')
    # c.rotate_face('D', -1)
    # c.rotate_face('R', -1)
    # c.rotate_face('U')

    draw_interactive(Cube)

    plt.show()
