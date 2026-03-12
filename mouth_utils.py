from scipy.spatial import distance as dist

def mouth_aspect_ratio(mouth):

    A = dist.euclidean(mouth[1], mouth[7])
    B = dist.euclidean(mouth[2], mouth[6])
    C = dist.euclidean(mouth[3], mouth[5])

    D = dist.euclidean(mouth[0], mouth[4])

    mar = (A + B + C) / (3.0 * D)

    return mar