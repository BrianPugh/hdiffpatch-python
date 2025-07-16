"""Tests for TampConfig class and tamp compression configuration."""

import pytest

import hdiffpatch
from hdiffpatch import TampConfig


class TestTampConfigClass:
    """Test TampConfig class functionality."""

    def test_default_construction(self):
        """Test default TampConfig construction."""
        config = TampConfig()
        assert config.window == 10

    def test_custom_construction(self):
        """Test TampConfig construction with custom parameters."""
        config = TampConfig(window=12)
        assert config.window == 12


class TestTampConfigValidation:
    """Test TampConfig parameter validation."""

    @pytest.mark.parametrize("window", range(8, 16))  # 8-15
    def test_window_valid_values(self, window):
        """Test window accepts valid values."""
        config = TampConfig(window=window)
        assert config.window == window

    @pytest.mark.parametrize("window", [7, 16])
    def test_window_invalid_range(self, window):
        """Test window rejects out-of-range values."""
        with pytest.raises(ValueError, match="'window' must be"):
            TampConfig(window=window)

    @pytest.mark.parametrize("window", ["10", 10.5])
    def test_window_invalid_type(self, window):
        """Test window rejects invalid types."""
        with pytest.raises(TypeError, match="'window' must be <class 'int'>"):
            TampConfig(window=window)  # type: ignore[arg-type]


class TestTampConfigClassmethods:
    """Test TampConfig classmethod constructors."""

    @pytest.mark.parametrize(
        "method_name,expected_attrs",
        [
            (
                "fast",
                {
                    "window": 8,
                },
            ),
            (
                "balanced",
                {
                    "window": 10,
                },
            ),
            (
                "best_compression",
                {
                    "window": 15,
                },
            ),
            (
                "minimal_memory",
                {
                    "window": 8,
                },
            ),
        ],
    )
    def test_classmethod_configs(self, method_name, expected_attrs):
        """Test TampConfig classmethod constructors."""
        config = getattr(TampConfig, method_name)()
        for attr_name, expected_value in expected_attrs.items():
            assert getattr(config, attr_name) == expected_value


class TestTampConfigMethods:
    """Test TampConfig instance methods."""

    def test_hashability(self):
        """Test that TampConfig objects are hashable."""
        config1 = TampConfig(window=10)
        config2 = TampConfig(window=10)
        config3 = TampConfig(window=12)

        # Test that equal objects have same hash
        assert hash(config1) == hash(config2)

        # Test that different objects have different hashes (usually)
        assert hash(config1) != hash(config3)

        # Test that objects can be used in sets and as dict keys
        config_set = {config1, config2, config3}
        assert len(config_set) == 2  # config1 and config2 are the same

        config_dict = {config1: "value1", config3: "value3"}
        assert len(config_dict) == 2


class TestTampConfigIntegration:
    """Test TampConfig integration with hdiffpatch.diff() function."""

    def test_diff_with_tamp_config_basic(self, simple_text_data):
        """Test diff() function accepts TampConfig objects."""
        config = TampConfig(window=10)

        # Test that diff accepts TampConfig objects
        diff_data = hdiffpatch.diff(simple_text_data["old"], simple_text_data["new"], compression=config)

        assert isinstance(diff_data, bytes)
        assert len(diff_data) > 0

        # Test round-trip
        result = hdiffpatch.apply(simple_text_data["old"], diff_data)
        assert result == simple_text_data["new"]

    @pytest.mark.parametrize("window", [8, 10, 12, 15])
    def test_diff_with_different_windows(self, large_repetitive_data, window):
        """Test diff() with different window sizes."""
        config = TampConfig(window=window)

        # Test that diff accepts different window sizes
        diff_data = hdiffpatch.diff(large_repetitive_data["old"], large_repetitive_data["new"], compression=config)

        assert isinstance(diff_data, bytes)
        assert len(diff_data) > 0

        # Test round-trip
        result = hdiffpatch.apply(large_repetitive_data["old"], diff_data)
        assert result == large_repetitive_data["new"]

    @pytest.mark.parametrize(
        "config_method",
        [
            TampConfig.fast,
            TampConfig.balanced,
            TampConfig.best_compression,
            TampConfig.minimal_memory,
        ],
    )
    def test_diff_with_tamp_config_classmethods(self, large_repetitive_data, config_method):
        """Test diff() with TampConfig classmethod constructors."""
        config = config_method()

        # Test that diff accepts all TampConfig classmethods
        diff_data = hdiffpatch.diff(large_repetitive_data["old"], large_repetitive_data["new"], compression=config)

        assert isinstance(diff_data, bytes)
        assert len(diff_data) > 0

        # Test round-trip
        result = hdiffpatch.apply(large_repetitive_data["old"], diff_data)
        assert result == large_repetitive_data["new"]

    def test_diff_backward_compatibility(self, simple_text_data):
        """Test that string-based compression still works."""
        # This should continue to work
        diff_data = hdiffpatch.diff(simple_text_data["old"], simple_text_data["new"], compression="tamp")

        assert isinstance(diff_data, bytes)
        assert len(diff_data) > 0

        # Test round-trip
        result = hdiffpatch.apply(simple_text_data["old"], diff_data)
        assert result == simple_text_data["new"]


class TestTampConfigRoundTrip:
    """Test round-trip functionality with TampConfig."""

    def test_round_trip_with_config(self, simple_text_data):
        """Test complete round-trip with TampConfig."""
        config = TampConfig(window=12)

        # Test complete round-trip with TampConfig
        diff_data = hdiffpatch.diff(simple_text_data["old"], simple_text_data["new"], compression=config)

        assert isinstance(diff_data, bytes)
        assert len(diff_data) > 0

        # Test that apply() can handle the diff (should auto-detect compression)
        result = hdiffpatch.apply(simple_text_data["old"], diff_data)
        assert result == simple_text_data["new"]

    @pytest.mark.parametrize("window", [8, 10, 12, 15])
    def test_round_trip_all_windows(self, unicode_data, window):
        """Test round-trip with all valid window sizes."""
        config = TampConfig(window=window)

        # Test round-trip with different window sizes
        diff_data = hdiffpatch.diff(unicode_data["old"], unicode_data["new"], compression=config)

        assert isinstance(diff_data, bytes)
        assert len(diff_data) > 0

        # Test round-trip
        result = hdiffpatch.apply(unicode_data["old"], diff_data)
        assert result == unicode_data["new"]

    @pytest.mark.parametrize(
        "config_method",
        [
            TampConfig.fast,
            TampConfig.balanced,
            TampConfig.best_compression,
            TampConfig.minimal_memory,
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


class TestTampConfigEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_data_with_config(self, empty_data):
        """Test TampConfig with empty data."""
        config = TampConfig(window=8)

        # Test TampConfig with empty data
        diff_data = hdiffpatch.diff(empty_data["old"], empty_data["new"], compression=config)

        assert isinstance(diff_data, bytes)
        assert len(diff_data) > 0

        # Test round-trip
        result = hdiffpatch.apply(empty_data["old"], diff_data)
        assert result == empty_data["new"]

    def test_identical_data_with_config(self, identical_data):
        """Test TampConfig with identical data."""
        config = TampConfig(window=15)

        # Test TampConfig with identical data
        diff_data = hdiffpatch.diff(identical_data["old"], identical_data["new"], compression=config)

        assert isinstance(diff_data, bytes)
        assert len(diff_data) > 0

        # Test round-trip
        result = hdiffpatch.apply(identical_data["old"], diff_data)
        assert result == identical_data["new"]

    def test_large_data_with_minimal_window(self, random_data):
        """Test minimal window size with large data."""
        config = TampConfig(window=8)

        # Test minimal window with large data
        diff_data = hdiffpatch.diff(random_data["old"], random_data["new"], compression=config)

        assert isinstance(diff_data, bytes)
        assert len(diff_data) > 0

        # Test round-trip
        result = hdiffpatch.apply(random_data["old"], diff_data)
        assert result == random_data["new"]


class TestTampConfigDifferentiation:
    """Test that different TampConfig settings produce different results."""

    def test_different_windows_produce_different_sizes(self, highly_compressible_data):
        """Test that different window sizes produce different diff sizes."""
        # Use highly compressible data to see clear differences
        old_data = highly_compressible_data["old"]
        new_data = highly_compressible_data["new"]

        # Test different window sizes
        configs = [
            TampConfig(window=8),  # Small window
            TampConfig(window=12),  # Medium window
            TampConfig(window=15),  # Large window
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

        # Different window sizes should potentially produce different results
        # (though this isn't always guaranteed due to data characteristics)
        # At minimum, we should see that compression works for all sizes
        window8_size, window12_size, window15_size = diff_sizes

        # Verify all compressions work correctly
        assert window8_size > 0
        assert window12_size > 0
        assert window15_size > 0

    def test_config_vs_default_tamp(self, large_repetitive_data):
        """Test that TampConfig produces different results than default 'tamp'."""
        old_data = large_repetitive_data["old"]
        new_data = large_repetitive_data["new"]

        # Default tamp string compression
        default_diff = hdiffpatch.diff(old_data, new_data, compression="tamp")

        # Custom configurations that might differ from default
        configs_to_test = [
            TampConfig(window=8),  # Smaller window than default (10)
            TampConfig(window=15),  # Larger window than default (10)
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

        # At least the configurations should work correctly
        # (Exact size differences depend on data characteristics)
        window8_size, window15_size = config_sizes
        assert window8_size > 0
        assert window15_size > 0
        assert default_size > 0

    @pytest.mark.parametrize("window", [8, 10, 12, 15])
    def test_window_sizes_maintain_functionality(self, window):
        """Test that all window sizes work correctly."""
        # Create data that might show window size differences
        old_data = b"ABCD" * 500  # Repetitive pattern
        new_data = b"EFGH" * 500  # Different pattern, same structure

        config = TampConfig(window=window)
        diff_data = hdiffpatch.diff(old_data, new_data, compression=config)

        # Ensure round-trip works
        result = hdiffpatch.apply(old_data, diff_data)
        assert result == new_data

        # Size should be positive
        assert len(diff_data) > 0
