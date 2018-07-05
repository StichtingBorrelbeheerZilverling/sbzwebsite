import cProfile
import pstats


def profile(func):
    pr = cProfile.Profile()

    def result(*args, **kwargs):
        pr.enable()

        result = func(*args, **kwargs)

        pr.disable()
        stats = pstats.Stats(pr).sort_stats('cumulative')
        stats.print_stats()

        return result

    return result
