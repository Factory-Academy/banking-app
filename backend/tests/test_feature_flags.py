from app.utils.feature_flags import FeatureFlags


def test_feature_flag_defaults_when_missing():
    flags = FeatureFlags(env={})
    assert flags.enabled("fraud_amount_deviation_rule", default=True) is True
    assert flags.enabled("fraud_amount_deviation_rule", default=False) is False


def test_feature_flag_parses_truthy_values():
    flags = FeatureFlags(env={"FEATURE_FRAUD_AMOUNT_DEVIATION_RULE": "YeS"})
    assert flags.enabled("fraud_amount_deviation_rule") is True


def test_feature_flag_parses_falsy_values():
    flags = FeatureFlags(env={"FEATURE_FRAUD_AMOUNT_DEVIATION_RULE": "0"})
    assert flags.enabled("fraud_amount_deviation_rule", default=True) is False


def test_feature_flag_falls_back_to_default_for_unknown_values():
    flags = FeatureFlags(env={"FEATURE_FRAUD_AMOUNT_DEVIATION_RULE": "not-a-bool"})
    assert flags.enabled("fraud_amount_deviation_rule", default=True) is True
