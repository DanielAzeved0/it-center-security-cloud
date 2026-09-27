import time
from unittest.mock import patch

from app.repositories.machines import (
    STALE_THROTTLE_SECONDS,
    mark_stale_machines_offline,
    reset_stale_throttle_for_testing,
)


def test_mark_stale_machines_offline_throttled_for_global_calls():
    reset_stale_throttle_for_testing()

    with patch("app.repositories.machines.get_connection") as mock_conn:
        # Primeira chamada global: deve executar
        mark_stale_machines_offline(machine_id=None)
        assert mock_conn.call_count == 1

        # Segunda chamada global imediata: deve ser ignorada pelo throttle
        mark_stale_machines_offline(machine_id=None)
        assert mock_conn.call_count == 1

        # Chamada específica para machine_id: nunca sofre throttle
        mark_stale_machines_offline(machine_id=99)
        assert mock_conn.call_count == 2


def test_mark_stale_machines_offline_runs_after_throttle_interval():
    reset_stale_throttle_for_testing()

    with patch("app.repositories.machines.get_connection") as mock_conn, \
         patch("app.repositories.machines.time.monotonic") as mock_time:
        mock_time.return_value = 1000.0
        mark_stale_machines_offline(machine_id=None)
        assert mock_conn.call_count == 1

        # 10 seconds later: throttled
        mock_time.return_value = 1010.0
        mark_stale_machines_offline(machine_id=None)
        assert mock_conn.call_count == 1

        # 31 seconds later: executes
        mock_time.return_value = 1000.0 + STALE_THROTTLE_SECONDS + 1.0
        mark_stale_machines_offline(machine_id=None)
        assert mock_conn.call_count == 2
