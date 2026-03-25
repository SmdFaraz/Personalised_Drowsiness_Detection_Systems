import numpy as np
import mediapipe as mp

mp_face = mp.solutions.face_mesh

face_mesh = mp_face.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True
)


def get_face_embedding(frame):
    """
    Convert face landmarks → numeric embedding
    """

    rgb = frame[:, :, ::-1]
    results = face_mesh.process(rgb)

    if not results.multi_face_landmarks:
        return None

    landmarks = results.multi_face_landmarks[0]

    embedding = []

    for lm in landmarks.landmark:
        embedding.append([lm.x, lm.y, lm.z])

    embedding = np.array(embedding).flatten()

    # Normalize
    embedding = embedding / np.linalg.norm(embedding)

    return embedding


def compare_faces(known_embeddings, new_embedding, threshold=1.2):

    if len(known_embeddings) == 0 or new_embedding is None:
        return None

    distances = [
        np.linalg.norm(emb - new_embedding)
        for emb in known_embeddings
    ]

    min_dist = min(distances)

    if min_dist < threshold:
        return distances.index(min_dist)

    return None