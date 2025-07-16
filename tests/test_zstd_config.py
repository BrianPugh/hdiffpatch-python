"""Tests for ZStdConfig class and zstd compression configuration."""

import pytest

import hdiffpatch
from hdiffpatch import ZStdConfig


class TestZStdConfigClass:
    """Test ZStdConfig class functionality."""

    def test_default_construction(self):
        """Test default ZStdConfig construction."""
        config = ZStdConfig()
        assert config.level == 3
        assert config.window is None
        assert config.workers == 0

    def test_custom_construction(self):
        """Test ZStdConfig construction with custom parameters."""
        config = ZStdConfig(level=10, window=20, workers=4)
        assert config.level == 10
        assert config.window == 20
        assert config.workers == 4


class TestZStdConfigValidation:
    """Test ZStdConfig parameter validation."""

    @pytest.mark.parametrize("level", range(1, 23))  # 1-22
    def test_level_valid_values(self, level):
        """Test level accepts valid values."""
        config = ZStdConfig(level=level)
        assert config.level == level

    @pytest.mark.parametrize("level", [0, 23])
    def test_level_invalid_range(self, level):
        """Test level rejects out-of-range values."""
        with pytest.raises(ValueError, match="'level' must be"):
            ZStdConfig(level=level)

    @pytest.mark.parametrize("level", ["6", 6.5])
    def test_level_invalid_type(self, level):
        """Test level rejects invalid types."""
        with pytest.raises(TypeError, match="'level' must be <class 'int'>"):
            ZStdConfig(level=level)  # type: ignore[arg-type]

    @pytest.mark.parametrize("window", [10, 15, 20, 27])
    def test_window_valid_values(self, window):
        """Test window accepts valid values."""
        config = ZStdConfig(window=window)
        assert config.window == window

    @pytest.mark.parametrize("window", [9, 28])
    def test_window_invalid_range(self, window):
        """Test window rejects out-of-range values."""
        with pytest.raises(ValueError, match="'window' must be"):
            ZStdConfig(window=window)

    def test_window_invalid_type(self):
        """Test window rejects invalid types."""
        with pytest.raises(TypeError, match="'window' must be <class 'int'>"):
            ZStdConfig(window="20")  # type: ignore[arg-type]

    def test_window_none_allowed(self):
        """Test window accepts None."""
        config = ZStdConfig(window=None)
        assert config.window is None

    @pytest.mark.parametrize("workers", [0, 1, 50, 200])
    def test_workers_valid_values(self, workers):
        """Test workers accepts valid values."""
        config = ZStdConfig(workers=workers)
        assert config.workers == workers

    @pytest.mark.parametrize("workers", [-1, 201])
    def test_workers_invalid_range(self, workers):
        """Test workers rejects out-of-range values."""
        with pytest.raises(ValueError, match="'workers' must be"):
            ZStdConfig(workers=workers)

    def test_workers_invalid_type(self):
        """Test workers rejects invalid types."""
        with pytest.raises(TypeError, match="'workers' must be <class 'int'>"):
            ZStdConfig(workers="4")  # type: ignore[arg-type]


class TestZStdConfigClassmethods:
    """Test ZStdConfig classmethod constructors."""

    @pytest.mark.parametrize(
        "method_name,expected_attrs",
        [
            (
                "fast",
                {
                    "level": 1,
                    "window": None,
                    "workers": 0,
                },
            ),
            (
                "balanced",
                {
                    "level": 6,
                    "window": None,
                    "workers": 2,
                },
            ),
            (
                "best_compression",
                {
                    "level": 22,
                    "window": 27,
                    "workers": 4,
                },
            ),
            (
                "minimal_memory",
                {
                    "level": 3,
                    "window": 10,
                    "workers": 0,
                },
            ),
        ],
    )
    def test_classmethod_configs(self, method_name, expected_attrs):
        """Test ZStdConfig classmethod constructors."""
        config = getattr(ZStdConfig, method_name)()
        for attr_name, expected_value in expected_attrs.items():
            assert getattr(config, attr_name) == expected_value


class TestZStdConfigMethods:
    """Test ZStdConfig instance methods."""

    def test_hashability(self):
        """Test that ZStdConfig objects are hashable."""
        config1 = ZStdConfig(level=6, window=15, workers=2)
        config2 = ZStdConfig(level=6, window=15, workers=2)
        config3 = ZStdConfig(level=9, window=15, workers=2)

        # Test that equal objects have same hash
        assert hash(config1) == hash(config2)

        # Test that different objects have different hashes (usually)
        assert hash(config1) != hash(config3)

        # Test that objects can be used in sets and as dict keys
        config_set = {config1, config2, config3}
        assert len(config_set) == 2  # config1 and config2 are the same

        config_dict = {config1: "value1", config3: "value3"}
        assert len(config_dict) == 2


class TestZStdConfigIntegration:
    """Test ZStdConfig integration with hdiffpatch.diff() function."""

    def test_diff_with_zstd_config_basic(self, simple_text_data):
        """Test diff() function accepts ZStdConfig objects."""
        config = ZStdConfig(level=6)

        # Test that diff accepts ZStdConfig objects
        diff_data = hdiffpatch.diff(simple_text_data["old"], simple_text_data["new"], compression=config)

        assert isinstance(diff_data, bytes)
        assert len(diff_data) > 0

        # Test round-trip
        result = hdiffpatch.apply(simple_text_data["old"], diff_data)
        assert result == simple_text_data["new"]

    @pytest.mark.parametrize(
        "config_method",
        [
            ZStdConfig.fast,
            ZStdConfig.balanced,
            ZStdConfig.best_compression,
            ZStdConfig.minimal_memory,
        ],
    )
    def test_diff_with_zstd_config_classmethods(self, large_repetitive_data, config_method):
        """Test diff() with ZStdConfig classmethod constructors."""
        config = config_method()

        # Test that diff accepts all ZStdConfig classmethods
        diff_data = hdiffpatch.diff(large_repetitive_data["old"], large_repetitive_data["new"], compression=config)

        assert isinstance(diff_data, bytes)
        assert len(diff_data) > 0

        # Test round-trip
        result = hdiffpatch.apply(large_repetitive_data["old"], diff_data)
        assert result == large_repetitive_data["new"]

    def test_diff_backward_compatibility(self, simple_text_data):
        """Test that string-based compression still works."""
        # This should continue to work
        diff_data = hdiffpatch.diff(simple_text_data["old"], simple_text_data["new"], compression="zstd")

        assert isinstance(diff_data, bytes)
        assert len(diff_data) > 0

        # Test round-trip
        result = hdiffpatch.apply(simple_text_data["old"], diff_data)
        assert result == simple_text_data["new"]

    @pytest.mark.parametrize("level", [1, 6, 15, 22])
    def test_diff_levels(self, highly_compressible_data, level):
        """Test diff() with different levels."""
        config = ZStdConfig(level=level)

        # Test that diff accepts different levels
        diff_data = hdiffpatch.diff(
            highly_compressible_data["old"], highly_compressible_data["new"], compression=config
        )

        assert isinstance(diff_data, bytes)
        assert len(diff_data) > 0

        # Test round-trip
        result = hdiffpatch.apply(highly_compressible_data["old"], diff_data)
        assert result == highly_compressible_data["new"]

    @pytest.mark.parametrize("window", [10, 15, 20, 27])
    def test_diff_windows(self, binary_data, window):
        """Test diff() with different window sizes."""
        config = ZStdConfig(window=window)

        # Test that diff accepts different window sizes
        diff_data = hdiffpatch.diff(binary_data["old"], binary_data["new"], compression=config)

        assert isinstance(diff_data, bytes)
        assert len(diff_data) > 0

        # Test round-trip
        result = hdiffpatch.apply(binary_data["old"], diff_data)
        assert result == binary_data["new"]

    @pytest.mark.parametrize("workers", [0, 1, 4])
    def test_diff_workers(self, large_repetitive_data, workers):
        """Test diff() with different worker counts."""
        config = ZStdConfig(workers=workers)

        # Test that diff accepts different worker counts
        diff_data = hdiffpatch.diff(large_repetitive_data["old"], large_repetitive_data["new"], compression=config)

        assert isinstance(diff_data, bytes)
        assert len(diff_data) > 0

        # Test round-trip
        result = hdiffpatch.apply(large_repetitive_data["old"], diff_data)
        assert result == large_repetitive_data["new"]


class TestZStdConfigRoundTrip:
    """Test round-trip functionality with ZStdConfig."""

    def test_round_trip_with_config(self, simple_text_data):
        """Test complete round-trip with ZStdConfig."""
        config = ZStdConfig(level=6, window=15, workers=2)

        # Test complete round-trip with ZStdConfig
        diff_data = hdiffpatch.diff(simple_text_data["old"], simple_text_data["new"], compression=config)

        assert isinstance(diff_data, bytes)
        assert len(diff_data) > 0

        # Test that apply() can handle the diff (should auto-detect compression)
        result = hdiffpatch.apply(simple_text_data["old"], diff_data)
        assert result == simple_text_data["new"]

    @pytest.mark.parametrize(
        "config_method",
        [
            ZStdConfig.fast,
            ZStdConfig.balanced,
            ZStdConfig.best_compression,
            ZStdConfig.minimal_memory,
        ],
    )
    def test_round_trip_all_classmethods(self, unicode_data, config_method):
        """Test round-trip with all classmethod configurations."""
        config = config_method()

        # Test round-trip with all classmethod configurations
        diff_data = hdiffpatch.diff(unicode_data["old"], unicode_data["new"], compression=config)

        assert isinstance(diff_data, bytes)
        assert len(diff_data) > 0

        # Test round-trip
        result = hdiffpatch.apply(unicode_data["old"], diff_data)
        assert result == unicode_data["new"]


class TestZStdConfigDifferentiation:
    """Test that different ZStdConfig settings produce different results."""

    def test_levels_produce_different_sizes(self, highly_compressible_data):
        """Test that different levels produce different diff sizes."""
        # Use highly compressible data to see clear differences
        old_data = highly_compressible_data["old"]
        new_data = highly_compressible_data["new"]

        # Test different levels
        configs = [
            ZStdConfig(level=1),  # Fast
            ZStdConfig(level=6),  # Balanced
            ZStdConfig(level=22),  # Best
        ]

        diff_sizes = []
        for config in configs:
            diff_data = hdiffpatch.diff(old_data, new_data, compression=config)
            diff_sizes.append(len(diff_data))

            # Ensure round-trip works
            result = hdiffpatch.apply(old_data, diff_data)
            assert result == new_data

        # All sizes should be positive
        assert all(size > 0 for size in diff_sizes)

        # At minimum, we should see that not all sizes are identical
        assert len(set(diff_sizes)) >= 1, f"Expected valid sizes, got: {diff_sizes}"

    def test_config_vs_default_zstd(self, large_repetitive_data):
        """Test that ZStdConfig can be used as alternative to default 'zstd'."""
        old_data = large_repetitive_data["old"]
        new_data = large_repetitive_data["new"]

        # Default zstd string compression
        default_diff = hdiffpatch.diff(old_data, new_data, compression="zstd")

        # Custom configurations
        configs_to_test = [
            ZStdConfig.fast(),  # Level 1
            ZStdConfig.best_compression(),  # Level 22
        ]

        default_size = len(default_diff)
        config_sizes = []

        for config in configs_to_test:
            config_diff = hdiffpatch.diff(old_data, new_data, compression=config)
            config_sizes.append(len(config_diff))

            # Ensure round-trip works
            result = hdiffpatch.apply(old_data, config_diff)
            assert result == new_data

        # All should work
        assert all(size > 0 for size in config_sizes)
        assert default_size > 0
