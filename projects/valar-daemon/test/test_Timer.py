"""Test that the Timer is running correctly.
"""
import time
import pytest

from valar_daemon.Timer import Timer


class TestTimer():


    @staticmethod
    @pytest.mark.parametrize(
        "period_s, num_of_tests", 
        [
            (2, 3),
            (3, 3),
        ]
    )
    def test_timer_normal_operation(
        period_s: int,
        num_of_tests: int
    ):
        """Test if the timer correctly waits for the desired amount of time.

        Parameters
        ----------
        period_s : int
            Timer period in seconds.
        num_of_tests : int
            Number of test instances that are carried out (repetitions).
        """
        for i in range(num_of_tests):
            timer = Timer(period_s=period_s)
            timer.reset_timer()
            assert not timer.has_time_window_elapsed()
            for n in range(period_s-1):
                time.sleep(1)
                assert not timer.has_time_window_elapsed()
            time.sleep(1)
            assert timer.has_time_window_elapsed()


    @staticmethod
    def test_timer_without_reset():
        """Test if the timer is by default elapsed in case it is not reset after initialization.
        """
        timer = Timer(period_s=3)
        assert timer.has_time_window_elapsed()
