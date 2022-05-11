def Rotate_s(sequence, s):

    sticker_n = s

    _sequence = sequence  # sequence

    for f in _sequence:

        if f == 'U':
            for i in [47, 50, 53]:
                u = sticker_n[i - 27]
                sticker_n[i - 27] = sticker_n[i]
                sticker_n[i] = sticker_n[i - 18]
                sticker_n[i - 18] = sticker_n[i - 9]
                sticker_n[i - 9] = u

            t1 = sticker_n[0]
            t2 = sticker_n[1]
            t3 = sticker_n[2]

            sticker_n[0] = t3
            sticker_n[1] = sticker_n[5]
            sticker_n[2] = sticker_n[8]

            sticker_n[5] = sticker_n[7]
            sticker_n[8] = sticker_n[6]

            sticker_n[7] = sticker_n[3]
            sticker_n[6] = t1
            sticker_n[3] = t2

        elif f == 'D':
            for i in [45, 48, 51]:
                d = sticker_n[i]
                sticker_n[i] = sticker_n[i - 27]
                sticker_n[i - 27] = sticker_n[i - 9]
                sticker_n[i - 9] = sticker_n[i - 18]
                sticker_n[i - 18] = d

            t1 = sticker_n[9]
            t2 = sticker_n[10]
            t3 = sticker_n[11]

            sticker_n[9] = sticker_n[15]
            sticker_n[10] = sticker_n[12]
            sticker_n[11] = t1

            sticker_n[12] = sticker_n[16]
            sticker_n[15] = sticker_n[17]

            sticker_n[16] = sticker_n[14]
            sticker_n[17] = t3
            sticker_n[14] = t2

        elif f == 'L':
            for i in range(3):
                l = sticker_n[47 - i]
                sticker_n[47 - i] = sticker_n[0 + i]
                sticker_n[0 + i] = sticker_n[42 + i]
                sticker_n[42 + i] = sticker_n[11 - i]
                sticker_n[11 - i] = l

            t1 = sticker_n[18]
            t2 = sticker_n[19]
            t3 = sticker_n[20]

            sticker_n[18] = sticker_n[24]
            sticker_n[19] = sticker_n[21]
            sticker_n[20] = t1

            sticker_n[24] = sticker_n[26]
            sticker_n[21] = sticker_n[25]

            sticker_n[26] = t3
            sticker_n[25] = sticker_n[23]
            sticker_n[23] = t2

        elif f == 'R':
            for i in range(3):
                r = sticker_n[51 + i]
                sticker_n[51 + i] = sticker_n[15 + i]
                sticker_n[15 + i] = sticker_n[38 - i]
                sticker_n[38 - i] = sticker_n[8 - i]
                sticker_n[8 - i] = r

            t1 = sticker_n[27]
            t2 = sticker_n[28]
            t3 = sticker_n[29]

            sticker_n[27] = sticker_n[33]
            sticker_n[28] = sticker_n[30]
            sticker_n[29] = t1

            sticker_n[33] = sticker_n[35]
            sticker_n[30] = sticker_n[34]

            sticker_n[35] = t3
            sticker_n[34] = sticker_n[32]
            sticker_n[32] = t2

        elif f == 'B':
            for i in range(3):
                b = sticker_n[i * 3]
                sticker_n[i * 3] = sticker_n[35 - i]
                sticker_n[35 - i] = sticker_n[15 - i * 3]
                sticker_n[15 - i * 3] = sticker_n[18 + i]
                sticker_n[18 + i] = b

            t1 = sticker_n[36]
            t2 = sticker_n[37]
            t3 = sticker_n[38]

            sticker_n[36] = sticker_n[42]
            sticker_n[37] = sticker_n[39]
            sticker_n[38] = t1

            sticker_n[42] = sticker_n[44]
            sticker_n[39] = sticker_n[43]

            sticker_n[44] = t3
            sticker_n[43] = sticker_n[41]
            sticker_n[41] = t2

        elif f == 'F':
            for i in range(3):
                f = sticker_n[2 + 3 * i]
                sticker_n[2 + i * 3] = sticker_n[24 + i]
                sticker_n[24 + i] = sticker_n[17 - i * 3]
                sticker_n[17 - i * 3] = sticker_n[29 - i]
                sticker_n[29 - i] = f

            t1 = sticker_n[45]
            t2 = sticker_n[46]
            t3 = sticker_n[47]

            sticker_n[45] = sticker_n[51]
            sticker_n[46] = sticker_n[48]
            sticker_n[47] = t1

            sticker_n[51] = sticker_n[53]
            sticker_n[48] = sticker_n[52]

            sticker_n[53] = t3
            sticker_n[52] = sticker_n[50]
            sticker_n[50] = t2

    return sticker_n
