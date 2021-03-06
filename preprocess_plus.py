from __future__ import print_function
import os
import sys
import numpy as np
from tqdm import tqdm
from preprocess import normalize

## VAD Parameters ##
VAD_THRESHOLD = -80  # if a frame has no filter that exceeds this threshold, it is assumed silent and removed
VAD_NFRAMES = 150  # if a filtered utterance is shorter than this after VAD, the full utterance is retained

assert (VAD_THRESHOLD >= -100.0)
assert (VAD_NFRAMES >= 1)


def bulk_VAD(feats):
    return [normalize(VAD(utt, i)) for i, utt in enumerate(tqdm(feats))]


def VAD(utterance, obs_idx):
    """
    The utterances may contain silence segments. These are clearly not useful for training (or during testing),
    and it is critical that they are filtered out in a preprocessing stage. This stage, in which we only retain
    frames that are detected to contain speech, is referred to as Voice Activity Detection (VAD).
    One simple way to apply VAD is to remove a frame if the maximum filter intensity is below some sensible
    threshold.
    :param utterance:
    :return: filtered utterance
    """
    filtered = utterance[utterance.max(axis=1) > VAD_THRESHOLD]
    if len(filtered) == 0:
        print('Observation number {} has no values above VAD treshold. Selecting top values...'.format(obs_idx))
        filtered = utterance[np.argpartition(-utterance.max(axis=1), range(VAD_NFRAMES))[:VAD_NFRAMES]]
        filtered = select_random_frames(filtered, VAD_NFRAMES)
    filtered = select_random_frames(filtered, VAD_NFRAMES)
    return filtered


def pad_pattern_end(x, l):
    """
    Pad the array to that of the maximum length by adding the reversed order up to length l.
    :param x: x is a 2-dimensional int numpy array, (n, m)
    :param l: l is an integer representing the length of the utterances that the final array should be in.
    :return: 2-dimensional int numpy array.
    """
    assert len(x) > 0, 'Zero length encountered'
    x = np.concatenate([x, x[::-1]], axis=0)
    min_rep = (l + len(x) - 1) // len(x)
    x = np.concatenate([x] * min_rep, axis=0)
    x = x[:l]
    return x


def select_random_frames(x, l):
    """
    Select different parts of large utterances.
    :param x: 3-dimensional int numpy array, (n, ). First dimension of x is the number of instances in the array.
    Second dimension is variable, depending on the length of a given instance. Third dimension is fixed
    to the number of features extracted per utterance in an instance.
    :param l: l is an integer representing the length of the utterances that the final array should be in.
    :return: 3-dimensional int numpy array of shape (n, l, -1)
    """
    x = [pad_pattern_end(i, l) for i in x]
    x = [i[np.random.randint(low=0, high=len(i) - l + 1) if len(i) > l else 0:][:l] for i in x]
    return np.array(x)


# data = [
# [ [1,2], [3,4], [4,5], [5,6], [1,2], [3,4], [4,5], [5,6], [1,2], [3,4], [4,5], [5,6]],
# [ [1,7], [2,8], [3, 10] ],
# [ [1,1] ]
# ]
# # data = [
# #     [1,2,3],
# #     [5,6,]
# # ]
# print([len(i) for i in select_random_frames(data, 15)])
# print(select_random_frames(data, 15))

if __name__ == "__main__":
    # if len(sys.argv) < 3 or sys.argv[2] not in list(map(str, range(1, 7))) + ["dev", "test"]:
    #     print("Usage:", sys.argv[0], "<path to npz files>", "<chunk among {1, 2, .., 6, dev, test}>")
    #     exit(0)

    # path, part = sys.argv[1], sys.argv[2]
    path = './data'
    part = '1'
    input_path = os.path.join(path, part + ".npz")
    output_path = os.path.join(path, part + ".preprocessed.npz")

    npz = np.load(input_path, encoding='latin1')
    if part == "dev":
        np.savez(output_path, enrol=bulk_VAD(npz['enrol']), test=bulk_VAD(npz['test']), trials=npz['trials'],
                 labels=npz['labels'])

    elif part == "test":
        np.savez(output_path, enrol=bulk_VAD(npz['enrol']), test=bulk_VAD(npz['test']), trials=npz['trials'])

    else:
        np.savez(output_path, feats=bulk_VAD(npz['feats']), targets=npz['targets'])
