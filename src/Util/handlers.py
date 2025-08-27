def verify_weights(weights : list[float]):
    if sum(weights) != 1:
        raise Exception("Sum of weights should be 1.")