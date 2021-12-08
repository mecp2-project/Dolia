# from https://www.mathworks.com/matlabcentral/fileexchange/3215-fit_ellipse
import numpy as np


def ellipse_fit(x, y):
    orientation_tolerance = 1e-3

    # remove bias of the ellipse - to make matrix inversion more accurate.
    mean_x = np.mean(x)
    mean_y = np.mean(y)

    x = x - mean_x
    y = y - mean_y

    # the estimation for the conic equation of the ellipse
    X = np.matrix(np.transpose([x * x, x * y, y * y, x, y]))

    # https://stackoverflow.com/a/59380798
    # in MATLAB: a = sum(X)/(X'*X);
    a_array = np.linalg.solve(
        (np.transpose(X) * X).conj().T,
        X.sum(axis=0).conj().T,
    ).conj().T

    # extract parameters from the conic equation
    a = a_array[0, 0]
    b = a_array[0, 1]
    c = a_array[0, 2]
    d = a_array[0, 3]
    e = a_array[0, 4]

    # remove the orientation from the ellipse
    if (min(abs(b / a), abs(b / c)) > orientation_tolerance):
        orientation_rad = 1 / 2 * np.arctan(b / (c - a))
        cos_phi = np.cos(orientation_rad)
        sin_phi = np.sin(orientation_rad)

        a, b, c, d, e = [
            a * cos_phi**2 - b * cos_phi * sin_phi + c * sin_phi**2,
            0,
            a * sin_phi**2 + b * cos_phi * sin_phi + c * cos_phi**2,
            d * cos_phi - e * sin_phi,
            d * sin_phi + e * cos_phi,
        ]

        mean_x, mean_y = [
            cos_phi * mean_x - sin_phi * mean_y,
            sin_phi * mean_x + cos_phi * mean_y,
        ]
    else:
        orientation_rad = 0
        cos_phi = np.cos(orientation_rad)
        sin_phi = np.sin(orientation_rad)

    # check if conic equation represents an ellipse
    test = a * c

    # if we found an ellipse return it's data
    if test > 0:
        # make sure coefficients are positive as required
        if a < 0:
            a, c, d, e = [-a, -c, -d, -e]
        # final ellipse parameters
        # yapf: disable
        X0         = mean_x - d / 2 / a
        Y0         = mean_y - e / 2 / c
        F          = 1 + (d**2) / (4 * a) + (e**2) / (4 * c)
        a, b       = [np.sqrt(F / a), np.sqrt(F / c)]
        long_axis  = 2 * max(a, b)
        short_axis = 2 * min(a, b)
        # rotate the axes backwards to find the center point of the original TILTED ellipse
        R          = np.array([[cos_phi, sin_phi], [-sin_phi, cos_phi]])
        P_in       = R * np.matrix([X0, Y0]).T
        X0_in      = P_in[0, 0]
        Y0_in      = P_in[1, 0]
        # yapf: enable
        # pack ellipse into a structure
        return True, {
            'a': a,
            'b': b,
            'phi': orientation_rad,
            'Y0': Y0,
            'X0_in': X0_in,
            'Y0_in': Y0_in,
            'long_axis': long_axis,
            'short_axis': short_axis,
        }
    else:
        return False, {}


if __name__ == "__main__":
    print(
        ellipse_fit(
            np.array([
                84.31013488769530, 68.53809356689450, 60.047096252441400,
                63.417667388916000, 77.90740966796880
            ]),
            np.array([
                70.13572692871090, 76.12509155273440, 90.2508544921875,
                106.88512420654300, 117.60356903076200
            ])))
