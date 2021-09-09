import numpy as np
import matplotlib.pyplot as plt
import random
from matplotlib import widgets
from projection import Quaternion, project_points
from PIL import Image
import glob
from data import Cube
from Rotate import Rotate_s


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



        self._ax_white_corner = self.figure.add_axes([0.8, 0.9, 0.2, 0.050])
        self._btn_white_corner = widgets.Button(self._ax_white_corner, 'White corner')
        self._btn_white_corner.on_clicked(self.white_corner)

        self._ax_second_layer = self.figure.add_axes([0.8, 0.85, 0.2, 0.050])
        self._btn_second_layer = widgets.Button(self._ax_second_layer, 'second layer')
        self._btn_second_layer.on_clicked(self.second_layer)

        self._ax_yellow_cross = self.figure.add_axes([0.8, 0.80, 0.2, 0.050])
        self._btn_yellow_cross = widgets.Button(self._ax_yellow_cross, 'yellow cross')
        self._btn_yellow_cross.on_clicked(self.yellow_cross)

        self._ax_yellow_corner = self.figure.add_axes([0.8, 0.75, 0.2, 0.050])
        self._btn_yellow_corner = widgets.Button(self._ax_yellow_corner, 'yellow corner')
        self._btn_yellow_corner.on_clicked(self.yellow_corner)

        self._ax_permute_corners = self.figure.add_axes([0.8, 0.70, 0.2, 0.050])
        self._btn_permute_corners = widgets.Button(self._ax_permute_corners, 'permute corners')
        self._btn_permute_corners.on_clicked(self.permute_corners)

        self._ax_yellow_edges = self.figure.add_axes([0.8, 0.65, 0.2, 0.050])
        self._btn_yellow_edges = widgets.Button(self._ax_yellow_edges, 'yellow_edges')
        self._btn_yellow_edges.on_clicked(self.yellow_edges)



    def _project(self, pts):
        return project_points(pts, self._current_rot, self._view, [0, 1, 0])

    def _draw_cube(self):
        imgs = []
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

            if np.any(self._digit_flags[:3]):
                for d in np.arange(3)[self._digit_flags[:3]]:
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

        self.sequence = ['F', 'U', 'F', 'F', 'U', 'F', 'D', 'B', 'L', 'B', 'D', 'B', 'U', 'D', 'R', 'L', 'R', 'L', 'L',
                         'L']
        for i in range(20):
            self.cube.rotate_face(self.sequence[i])
        """
        self.sequence = [*range(50)]
        for i in range(50):  # 50
            s = random.choice(face)
            self.sequence[i] = s
            self.cube.rotate_face(s)
        """
        self.s = Rotate_s(self.sequence, self.s)
        print(self.sequence)
        print("scamble sequence:", self.s)
        self._draw_cube()

        return self.sequence

    def white_cross(self):
        move = []
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

        # l 到第一步
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
        print('move', move)

        for j in range(4):
            if 45 < self.s[48] < 53:
                self.rotate_once('F', self.s, move)
                self.rotate_once('F', self.s, move)
                break
            else:
                self.rotate_once('D', self.s, move)

        if self.s[5] == 5:
            for j in range(4):
                if 27 < self.s[30] < 35:
                    if self.s[16] == 7:
                        self.rotate_once('R', self.s, move)
                        self.rotate_once('R', self.s, move)
                        break
                    else:
                        self.rotate_once('D', self.s, move)
                else:
                    self.rotate_once('D', self.s, move)

            self.w = self.search_white(self.s)

            if self.s[7] == 7:
                for j in range(4):
                    if 36 < self.s[39] < 44:
                        if self.s[12] == 3:
                            self.rotate_once('B', self.s, move)
                            self.rotate_once('B', self.s, move)
                            break
                        else:
                            self.rotate_once('D', self.s, move)
                    else:
                        self.rotate_once('D', self.s, move)
                if self.s[3] == 3:
                    for j in range(4):
                        if 18 < self.s[21] < 26:
                            if self.s[10] == 1:
                                self.rotate_once('L', self.s, move)
                                self.rotate_once('L', self.s, move)
                                break
                            else:
                                self.rotate_once('D', self.s, move)
                        else:
                            self.rotate_once('D', self.s, move)
                else:
                    print('error 3')
            else:
                print('error 7')
        else:
            print('error f')

        self.move = move
        print('white cross move:', move)

    def wise_clock(self, w, edge_white, anti_step, move):
        self.edge_w(w, edge_white, anti_step, ['L', 'F', 'R', 'B'], [10, 14, 16, 12], move)

    def clock(self, w, edge_white, anti_step, move):
        self.top(w, edge_white, anti_step, ['F', 'L', 'B', 'R'], [14, 10, 12, 16], move)

    def edge_w(self, w, edge_white, anti_step, move_step, down, move):  # 找到4白色放到某四个位置

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

    def top(self, w, edge_white, anti_step, move_step, down, move):  # 找到4白色放到某四个位置

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

    def edge_r(self, w, edge_white, anti_step, move_step, down, move):  # 找到4白色放到某四个位置

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



    def pattern_1(self, f, d, s, move):  # single rotation lfrb

        if not s[d] in self.white_cross_List:
            self.rotate_face(f)
            self.s = Rotate_s(f, s)
            move.append(f)
        else:
            while s[d] in self.white_cross_List:
                self.rotate_face('D', s)
                s = Rotate_s('D', s)
                move.append('D')

            self.rotate_face(f)
            self.s = Rotate_s(f, s)

            move.append(f)

    def rotate_once(self, f, s, move):  # rotate f once
        self.rotate_face(f)
        self.s = Rotate_s(f, s)
        #move.append(f)

    def rotate_twice(self, f, s, move):
        self.rotate_once(f, s, move)
        self.rotate_once(f, s, move)

    def rotate_three(self, f, s, move):
        self.rotate_once(f, s, move)
        self.rotate_once(f, s, move)
        self.rotate_once(f, s, move)

    def search_white(self, s):
        w = []
        for i in range(53):
            if s[i] in self.white_cross_List:
                w.append(i)
        print("search:", w)
        return w

    def white_corner(self, move):
        while any(self.s[i] < 9 for i in [24, 42, 33, 51]):
            if all([self.s[1] == 1, self.s[3] == 3, self.s[5] == 5, self.s[7] == 7]):
                self.white_corner_pattern3([42, 24, 33, 51], 1, move)

        while any(self.s[i] < 9 for i in [9, 11, 15, 17]):
            self.white_corner_pattern3([9, 11, 15, 17], 3, move)

        while any(self.s[i] < 9 for i in [18, 45, 36, 27]):
            self.white_corner_pattern3([18, 45, 36, 27], 5, move)

        while any(self.s[i] < 9 for i in [9, 11, 15, 17, 18, 45, 36, 27, 24, 42, 33, 51]):
            while any(self.s[i] < 9 for i in [24, 42, 33, 51]):
                self.white_corner_pattern3([42, 24, 33, 51], 1, move)

            while any(self.s[i] < 9 for i in [9, 11, 15, 17]):
                self.white_corner_pattern3([9, 11, 15, 17], 3, move)

            while any(self.s[i] < 9 for i in [18, 45, 36, 27]):
                self.white_corner_pattern3([18, 45, 36, 27], 5, move)

        # bottom2
        self.white_corner_bottom_2(44, 0, 'B', 2, move)
        self.white_corner_bottom_2(26, 2, 'L', 2, move)
        self.white_corner_bottom_2(35, 6, 'R', 2, move)
        self.white_corner_bottom_2(53, 8, 'F', 2, move)

        if all([self.s[1] == 1, self.s[3] == 3, self.s[5] == 5, self.s[7] == 7]):
            print("good")

            # bottom4

            self.white_corner_bottom_2(20, 0, 'B', 4, move)
            self.white_corner_bottom_2(47, 2, 'L', 4, move)
            self.white_corner_bottom_2(29, 6, 'R', 4, move)

            for i in range(9):
                if self.s[i] == i:
                    break
                else:
                    self.white_corner_bottom_2(38, 8, 'F', 4, move)

            if all([self.s[i] == i for i in range(9)]):
                print("white corner move:", move)
            else:
                print("white corner wrong!")

        else:
            print("error bottom 2")

    def white_corner_bottom_2(self, i, white, f, n, move):
        if self.s[i] < 9:
            if self.s[i] == white:
                for j in range(n):
                    self.white_corner_s(f, move)

            else:
                self.white_corner_s(f, move)

                while any(self.s[i] < 9 for i in [24, 42, 33, 51]):
                    if all([self.s[1] == 1, self.s[3] == 3, self.s[5] == 5, self.s[7] == 7]):
                        self.white_corner_pattern3([42, 24, 33, 51], 1, move)

                while any(self.s[i] < 9 for i in [9, 11, 15, 17]):
                    self.white_corner_pattern3([9, 11, 15, 17], 3, move)

                while any(self.s[i] < 9 for i in [18, 45, 36, 27]):
                    self.white_corner_pattern3([18, 45, 36, 27], 5, move)

    def white_corner_pattern3(self, corner_n, times, move):  # 找到三种位置的白色，执行序列
        for i in corner_n:
            if self.s[i] < 9:
                if self.s[i] == 0:
                    for j in range(4):
                        if i == corner_n[0]:
                            for k in range(times):
                                self.white_corner_s('B', move)
                            break
                        else:
                            self.rotate_once('D', self.s, move)
                            for z in corner_n:
                                if self.s[z] == 0:
                                    i = z

                elif self.s[i] == 2:
                    for j in range(4):
                        if i == corner_n[1]:
                            for k in range(times):
                                self.white_corner_s('L', move)
                            break
                        else:
                            self.rotate_once('D', self.s, move)
                            for z in corner_n:
                                if self.s[z] == 2:
                                    i = z

                elif self.s[i] == 6:
                    for j in range(4):
                        if i == corner_n[2]:
                            for k in range(times):
                                self.white_corner_s('R', move)
                            break
                        else:
                            self.rotate_once('D', self.s, move)

                            for z in corner_n:
                                if self.s[z] == 6:
                                    i = z

                elif self.s[i] == 8:
                    for j in range(4):
                        if i == corner_n[3]:
                            for k in range(times):
                                self.white_corner_s('F', move)
                            break
                        else:
                            self.rotate_once('D', self.s, move)
                            for z in corner_n:
                                if self.s[z] == 8:
                                    i = z

    def white_corner_s(self, f, move):  # 上左下右
        self.rotate_once(f, self.s, move)
        self.rotate_once('D', self.s, move)
        self.rotate_three(f, self.s, move)
        self.rotate_three('D', self.s, move)

    def second_layer(self, move):

        self.second_layer_search()

        for i in range(10):
            if self.move:
                self.second_layer_search()
                self.top_edge_color(move)
                self.second_layer_s(move)
        print("second layer", move)

    def second_layer_search(self):

        k = 0
        for i in [10, 14, 16, 12]:
            self.edge = [21, 48, 30, 39]
            self.centre = [22, 49, 31, 40]

            self.top_edge = self.edge[k]
            self.top_centre = self.centre[k]
            self.k2 = k
            k = k + 1
            self.top_sticker = i
            if not self.color(self.s[i]) == 'yellow':
                if not self.color(self.s[self.top_edge]) == 'yellow':
                    self.second_sticker = True
                    break
                else:
                    self.second_sticker = False

    def top_edge_color(self, move):

        for j in range(4):
            # print("loop", self.color(self.s[self.top_edge]), self.color(self.s[self.top_centre]),
            # self.color(self.s[self.top_sticker]), self.top_edge,
            # self.top_centre)

            if self.color(self.s[self.top_centre]) == self.color(self.s[self.top_edge]):
                print("equal", self.top_edge, self.top_centre, self.color(self.s[self.top_edge]),
                      self.color(self.s[self.top_centre]), j)
                print("same color", self.color(self.s[self.top_edge]))
                break
            else:
                self.rotate_once('D', self.s, move)

                if not self.k2 < 3:
                    self.top_edge = self.edge[0]
                    self.top_centre = self.centre[0]
                else:
                    self.k2 = self.k2 + 1
                    self.top_edge = self.edge[self.k2]
                    self.top_centre = self.centre[self.k2]

    def second_layer_s(self, move):
        if self.s[self.top_centre == 22]:
            if self.s[self.top_edge] == 19:  # OK
                f = ['D', 'B', 'D', 'B', 'D', 'L', 'D', 'L']
                self.second_layer_1(f, move)
            elif self.s[self.top_edge] == 25:  # OK
                f = ['D', 'F', 'D', 'F', 'D', 'L', 'D', 'L']
                self.second_layer_2(f, move)

        elif self.s[self.top_centre == 40]:
            if self.s[self.top_edge] == 37:  # OK
                f = ['D', 'R', 'D', 'R', 'D', 'B', 'D', 'B']
                self.second_layer_1(f, move)
            elif self.s[self.top_edge] == 43:
                f = ['D', 'L', 'D', 'L', 'D', 'B', 'D', 'B']
                self.second_layer_2(f, move)

        elif self.s[self.top_centre == 31]:
            if self.s[self.top_edge] == 28:  # 公式1
                f = ['D', 'F', 'D', 'F', 'D', 'R', 'D', 'R']
                self.second_layer_1(f, move)
            elif self.s[self.top_edge] == 34:
                f = ['D', 'B', 'D', 'B', 'D', 'R', 'D', 'R']
                self.second_layer_2(f, move)

        elif self.s[self.top_centre == 49]:
            if self.s[self.top_edge] == 46:  # 公式1
                f = ['D', 'L', 'D', 'L', 'D', 'F', 'D', 'F']
                self.second_layer_1(f, move)
            elif self.s[self.top_edge] == 52:  # OK
                f = ['D', 'R', 'D', 'R', 'D', 'F', 'D', 'F']
                self.second_layer_2(f, move)

    def color(self, s1):  # 比较颜色是否相同
        if s1 in range(9):
            s1 = 'white'
        elif s1 in range(9, 18):
            s1 = 'yellow'
        elif s1 in range(18, 27):
            s1 = 'blue'
        elif s1 in range(27, 35):
            s1 = 'green'
        elif s1 in range(36, 44):
            s1 = 'orange'
        elif s1 in range(45, 53):
            s1 = 'red'
        return s1

    def second_layer_1(self, f, move):
        self.rotate_once(f[0], self.s, move)
        self.rotate_once(f[1], self.s, move)
        self.rotate_three(f[2], self.s, move)
        self.rotate_three(f[3], self.s, move)
        self.rotate_three(f[4], self.s, move)
        self.rotate_three(f[5], self.s, move)
        self.rotate_once(f[6], self.s, move)
        self.rotate_once(f[7], self.s, move)

    def second_layer_2(self, f, move):
        self.rotate_three(f[0], self.s, move)
        self.rotate_three(f[1], self.s, move)
        self.rotate_once(f[2], self.s, move)
        self.rotate_once(f[3], self.s, move)
        self.rotate_once(f[4], self.s, move)
        self.rotate_once(f[5], self.s, move)
        self.rotate_three(f[6], self.s, move)
        self.rotate_three(f[7], self.s, move)

    def yellow_cross(self, move):
        # 状态1
        if all([self.color(self.s[i]) != 'yellow' for i in [10, 12, 14, 16]]):
            self.yellow_cross_1(move)

        for i in range(4):
            if all([self.color(self.s[12]) == 'yellow', self.color(self.s[16]) == 'yellow']):
                # 状态2
                if all([self.color(self.s[10]) != 'yellow', self.color(self.s[14]) != 'yellow']):
                    self.yellow_cross_1(move)
                    break
            else:
                self.rotate_once('D', self.s, move)

        for i in range(4):
            if all([self.color(self.s[10]) == 'yellow', self.color(self.s[16]) == 'yellow']):
                print("10, 16")
                self.yellow_cross_1(move)
                break
            else:
                self.rotate_once('D', self.s, move)
                print("else")

    def yellow_cross_1(self, move):
        self.rotate_once('F', self.s, move)
        self.rotate_once('L', self.s, move)
        self.rotate_once('D', self.s, move)
        self.rotate_three('L', self.s, move)
        self.rotate_three('D', self.s, move)
        self.rotate_three('F', self.s, move)

    def yellow_corner(self, move):
        for i in range(4):
            if self.color(self.s[17]) == 'yellow':
                pass
            else:
                self.yellow_corner_s(move)
                self.yellow_corner_s(move)

                if self.color(self.s[17]) == 'yellow':
                    pass
                else:
                    self.yellow_corner_s(move)
                    self.yellow_corner_s(move)
            self.rotate_once('D', self.s, move)

    def yellow_corner_s(self, move):
        self.rotate_once('R', self.s, move)
        self.rotate_once('U', self.s, move)
        self.rotate_three('R', self.s, move)
        self.rotate_three('U', self.s, move)

    def permute_corners(self, move):
        if self.color(self.s[18]) == self.color(self.s[24]):
            f = ['R', 'D', 'R', 'D', 'R', 'B', 'R', 'R', 'D', 'R', 'D', 'R', 'D', 'R', 'B']
            self.permute_corners_s(f, move)

        elif self.color(self.s[45]) == self.color(self.s[51]):
            f = ['B', 'D', 'B', 'D', 'B', 'L', 'B', 'B', 'D', 'B', 'D', 'B', 'D', 'B', 'L']
            self.permute_corners_s(f, move)

        elif self.color(self.s[27]) == self.color(self.s[33]):
            f = ['L', 'D', 'L', 'D', 'L', 'F', 'L', 'L', 'D', 'L', 'D', 'L', 'D', 'L', 'F']
            self.permute_corners_s(f, move)

        elif self.color(self.s[36]) == self.color(self.s[42]):
            f = ['F', 'D', 'F', 'D', 'F', 'R', 'F', 'F', 'D', 'F', 'D', 'F', 'D', 'F', 'R']
            self.permute_corners_s(f, move)

        for i in range(4):
            if self.color(self.s[45]) == self.color(self.s[49]):
                break
            else:
                self.rotate_once('D', self.s, move)

    def permute_corners_s(self, f, move):

        self.rotate_once(f[0], self.s, move)

        self.rotate_once(f[1], self.s, move)
        self.rotate_three(f[2], self.s, move)
        self.rotate_three(f[3], self.s, move)

        self.rotate_three(f[4], self.s, move)
        self.rotate_once(f[5], self.s, move)
        self.rotate_once(f[6], self.s, move)
        self.rotate_once(f[7], self.s, move)
        self.rotate_three(f[8], self.s, move)

        self.rotate_three(f[9], self.s, move)
        self.rotate_three(f[10], self.s, move)
        self.rotate_once(f[11], self.s, move)
        self.rotate_once(f[12], self.s, move)
        self.rotate_three(f[13], self.s, move)

        self.rotate_three(f[14], self.s, move)

    def yellow_edges(self, move):
        if all([self.color(self.s[48]) != self.color(self.s[51]),
                self.color(self.s[30]) != self.color(self.s[33]),
                self.color(self.s[39]) != self.color(self.s[42]),
                self.color(self.s[21]) != self.color(self.s[24])]):
            self.yellow_edges_s('F', move)
        else:
            if all([self.color(self.s[48]) == self.color(self.s[51]),
                    self.color(self.s[30]) == self.color(self.s[33]),
                    self.color(self.s[39]) == self.color(self.s[42]),
                    self.color(self.s[21]) == self.color(self.s[24])]):
                pass
            else:

                if self.color(self.s[21]) == self.color(self.s[24]):
                    f = 'B'
                elif self.color(self.s[48]) == self.color(self.s[51]):
                    f = 'L'  # ['L', 'L', 'D', 'L', 'D', 'L', 'D', 'L', 'D', 'L', 'D', 'L']
                elif self.color(self.s[30]) == self.color(self.s[33]):
                    f = 'F'
                elif self.color(self.s[39]) != self.color(self.s[42]):
                    f = 'R'

                self.yellow_edges_s(f, move)
                if all([self.color(self.s[48]) == self.color(self.s[51]),
                        self.color(self.s[30]) == self.color(self.s[33]),
                        self.color(self.s[39]) == self.color(self.s[42]),
                        self.color(self.s[21]) == self.color(self.s[24])]):
                    print("solved")
                else:
                    self.yellow_edges_s(f, move)
                    print("success!")

    def yellow_edges_s(self, f, move):
        self.rotate_once(f, self.s, move)
        self.rotate_once(f, self.s, move)
        self.rotate_three('D', self.s, move)
        self.rotate_three(f, self.s, move)
        self.rotate_three('D', self.s, move)
        self.rotate_once(f, self.s, move)
        self.rotate_once('D', self.s, move)
        self.rotate_once(f, self.s, move)
        self.rotate_once('D', self.s, move)
        self.rotate_once(f, self.s, move)
        self.rotate_three('D', self.s, move)
        self.rotate_once(f, self.s, move)

        print("yellow")

    def _solve_cube(self, *args):
        self.white_cross()


        self.white_corner(self.move)

        self.second_layer(self.move)

        self.yellow_cross(self.move)

        self.yellow_corner(self.move)

        self.permute_corners(self.move)

        self.yellow_edges(self.move)
        plt.savefig('fo6.png')
        
        self._draw_cube()


if __name__ == '__main__':

    c = Cube()


    draw_interactive(Cube)


    plt.show()
