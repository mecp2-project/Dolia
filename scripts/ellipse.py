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
    a = np.linalg.solve(
        (np.transpose(X) * X).conj().T,
        X.sum(axis=0).conj().T,
    ).conj().T

    print(a)



if __name__ == "__main__":
    ellipse_fit(
        np.array([
            84.31013488769530, 68.53809356689450, 60.047096252441400,
            63.417667388916000, 77.90740966796880
        ]),
        np.array([
            70.13572692871090, 76.12509155273440, 90.2508544921875,
            106.88512420654300, 117.60356903076200
        ]))
