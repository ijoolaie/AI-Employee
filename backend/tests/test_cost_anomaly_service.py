from app.services.cost_anomaly_service import _anomaly


def test_cost_anomaly_detects_two_sigma_spike():
    anomaly, score = _anomaly(30.0, [10.0, 11.0, 9.0, 10.0, 12.0, 10.0, 11.0])
    assert anomaly is True
    assert score >= 2.0


def test_cost_anomaly_does_not_flag_normal_variation():
    anomaly, score = _anomaly(12.0, [10.0, 11.0, 9.0, 10.0, 12.0, 10.0, 11.0])
    assert anomaly is False
    assert score < 2.0


def test_cost_anomaly_handles_zero_baseline():
    anomaly, score = _anomaly(0.0, [0.0] * 7)
    assert anomaly is False
    assert score == 0.0
