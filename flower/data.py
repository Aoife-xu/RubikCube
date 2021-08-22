import numpy as np
import matplotlib.pyplot as plt
import random
from matplotlib import widgets
from projection import Quaternion, project_points


class Cube:
    """Magic Cube Representation"""
   # Define rotation angles and axes for the six sides of the cube

    default_plastic_color = 'black'  # the lines of the cube
    default_face_colors = ["white", "yellow",  # white, blue, yellow green, orange, red
                           "blue", "green",
                           "orange", "red",
                           "gray", "none"]

    base_face = np.array([[1, 1, 1],
                          [1, -1, 1],
                          [-1, -1, 1],
                          [-1, 1, 1],
                          [1, 1, 1]], dtype=float)

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
    base_sticker_centroid = np.array([[0, 0, 1 + stickerthickness]])
    x, y, z = np.eye(3)
    rots = [Quaternion.from_v_theta(np.eye(3)[0], theta)
            for theta in (np.pi / 2, -np.pi / 2)]
    rots += [Quaternion.from_v_theta(np.eye(3)[1], theta)
             for theta in (np.pi / 2, -np.pi / 2, np.pi, 2 * np.pi)]

    # define face movements
    facesdict = dict(F=z, B=-z,
                     R=x, L=-x,
                     U=y, D=-y)

    def __init__(self, N=3, plastic_color=None, face_colors=None):
        self.N = N
        if plastic_color is None:
            self.plastic_color = self.default_plastic_color
        else:
            self.plastic_color = plastic_color

        if face_colors is None:
            self.face_colors = self.default_face_colors
        else:
            self.face_colors = face_colors

        self._move_list = []
        self._initialize_arrays()

    def _initialize_arrays(self):
        # initialize centroids, faces, and stickers.  We start with a
        # base for each one, and then translate & rotate them into position.

        # Define 9 translations for each face of the cube
        cubie_width = 2. / 3
        translations = np.array([[[-1 + (i + 0.5) * cubie_width,
                                   -1 + (j + 0.5) * cubie_width, 0]]
                                 for i in range(3)
                                 for j in range(3)])

        # Create arrays for centroids, faces, stickers, and colors
        face_centroids = []
        faces = []
        sticker_centroids = []
        stickers = []
        colors = []

        factor = np.array([1. / 3, 1. / 3, 1])

        for i in range(6):
            M = self.rots[i].as_rotation_matrix()
            faces_t = np.dot(factor * self.base_face
                             + translations, M.T)
            stickers_t = np.dot(factor * self.base_sticker
                                + translations, M.T)
            face_centroids_t = np.dot(self.base_face_centroid
                                      + translations, M.T)
            sticker_centroids_t = np.dot(self.base_sticker_centroid
                                         + translations, M.T)
            colors_i = i + np.zeros(face_centroids_t.shape[0], dtype=int)

            # append face ID to the face centroids for lex-sorting
            face_centroids_t = np.hstack([face_centroids_t.reshape(-1, 3),
                                          colors_i[:, None]])
            sticker_centroids_t = sticker_centroids_t.reshape((-1, 3))

            faces.append(faces_t)
            face_centroids.append(face_centroids_t)
            stickers.append(stickers_t)
            sticker_centroids.append(sticker_centroids_t)
            colors.append(colors_i)

        self._face_centroids = np.vstack(face_centroids)
        self._faces = np.vstack(faces)
        self._sticker_centroids = np.vstack(sticker_centroids)
        self._stickers = np.vstack(stickers)
        self._colors = np.concatenate(colors)


    def rotate_face(self, f, n=1, layer=0):

        """Rotate Face"""
        if layer < 0 or layer >= 3:
            raise ValueError('layer should be between 0 and N-1')

        try:
            f_last, n_last, layer_last = self._move_list[-1]
        except:
            f_last, n_last, layer_last = None, None, None

        if (f == f_last) and (layer == layer_last):
            ntot = (n_last + n) % 4
            if abs(ntot - 4) < abs(ntot):
                ntot = ntot - 4
            if np.allclose(ntot, 0):
                self._move_list = self._move_list[:-1]
            else:
                self._move_list[-1] = (f, ntot, layer)
        else:
            self._move_list.append((f, n, layer))

        v =self.facesdict[f]
        r = Quaternion.from_v_theta(v, n * np.pi / 2)
        M = r.as_rotation_matrix()

        proj = np.dot(self._face_centroids[:, :3], v)
        cubie_width = 2. / 3
        flag = ((proj > 0.9 - (layer + 1) * cubie_width) &
                (proj < 1.1 - layer * cubie_width))


        for x in [self._stickers, self._sticker_centroids,
                  self._faces]:
            x[flag] = np.dot(x[flag], M.T)
        self._face_centroids[flag, :3] = np.dot(self._face_centroids[flag, :3],
                                                M.T)