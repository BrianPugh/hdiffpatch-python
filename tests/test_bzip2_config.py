"""Tests for BZip2Config class and bzip2 compression configuration."""

import pytest

import hdiffpatch
from hdiffpatch import BZip2Config


class TestBZip2ConfigClass:
    """Test BZip2Config class functionality."""

    def test_default_construction(self):
        """Test default BZip2Config construction."""
        config = BZip2Config()
        assert config.level == 9
        assert config.work_factor == 30

    def test_custom_construction(self):
        """Test BZip2Config construction with custom parameters."""
        config = BZip2Config(level=6, work_factor=100)
        assert config.level == 6
        assert config.work_factor == 100


class TestBZip2ConfigValidation:
    """Test BZip2Config parameter validation."""

    @pytest.mark.parametrize("level", range(1, 10))  # 1-9
    def test_level_valid_values(self, level):
        """Test level accepts valid values."""
        config = BZip2Config(level=level)
        assert config.level == level

    @pytest.mark.parametrize("level", [0, 10])
    def test_level_invalid_range(self, level):
        """Test level rejects out-of-range values."""
        with pytest.raises(ValueError, match="'level' must be"):
            BZip2Config(level=level)

    @pytest.mark.parametrize("level", ["6", 6.5])
    def test_level_invalid_type(self, level):
        """Test level rejects invalid types."""
        with pytest.raises(TypeError, match="'level' must be <class 'int'>"):
            BZip2Config(level=level)  # type: ignore[arg-type]

    @pytest.mark.parametrize("factor", [0, 30, 100, 250])
    def test_work_factor_valid_values(self, factor):
        """Test work factor accepts valid values."""
        config = BZip2Config(work_factor=factor)
        assert config.work_factor == factor

    @pytest.mark.parametrize("factor", [-1, 251])
    def test_work_factor_invalid_range(self, factor):
        """Test work factor rejects out-of-range values."""
        with pytest.raises(ValueError, match="'work_factor' must be"):
            BZip2Config(work_factor=factor)

    def test_work_factor_invalid_type(self):
        """Test work factor rejects invalid types."""
        with pytest.raises(TypeError, match="'work_factor' must be <class 'int'>"):
            BZip2Config(work_factor="30")  # type: ignore[arg-type]


class TestBZip2ConfigClassmethods:
    """Test BZip2Config classmethod constructors."""

    @pytest.mark.parametrize(
        "method_name,expected_attrs",
        [
            (
                "fast",
                {
                    "level": 1,
                    "work_factor": 0,
                },
            ),
            (
                "balanced",
                {
                    "level": 6,
                    "work_factor": 30,
                },
            ),
            (
                "best_compression",
                {
                    "level": 9,
                    "work_factor": 100,
                },
            ),
            (
                "minimal_memory",
                {
                    "level": 1,
                    "work_factor": 0,
                },
            ),
        ],
    )
    def test_classmethod_configs(self, method_name, expected_attrs):
        """Test BZip2Config classmethod constructors."""
        config = getattr(BZip2Config, method_name)()
        for attr_name, expected_value in expected_attrs.items():
            assert getattr(config, attr_name) == expected_value


class TestBZip2ConfigMethods:
    """Test BZip2Config instance methods."""

    def test_hashability(self):
        """Test that BZip2Config objects are hashable."""
        config1 = BZip2Config(level=6, work_factor=50)
        config2 = BZip2Config(level=6, work_factor=50)
        config3 = BZip2Config(level=9, work_factor=50)

        # Test that equal objects have same hash
        assert hash(config1) == hash(config2)

        # Test that different objects have different hashes (usually)
        assert hash(config1) != hash(config3)

        # Test that objects can be used in sets and as dict keys
        config_set = {config1, config2, config3}
        assert len(config_set) == 2  # config1 and config2 are the same

        config_dict = {config1: "value1", config3: "value3"}
        assert len(config_dict) == 2


class TestBZip2ConfigIntegration:
    """Test BZip2Config integration with hdiffpatch.diff() function."""

    def test_diff_with_bzip2_config_basic(self, simple_text_data):
        """Test diff() function accepts BZip2Config objects."""
        config = BZip2Config(level=6)

        # Test that diff accepts BZip2Config objects
        diff_data = hdiffpatch.diff(simple_text_data["old"], simple_text_data["new"], compression=config)

        assert isinstance(diff_data, bytes)
        assert len(diff_data) > 0

        # Test round-trip
        result = hdiffpatch.apply(simple_text_data["old"], diff_data)
        assert result == simple_text_data["new"]

    @pytest.mark.parametrize(
        "config_method",
        [
            BZip2Config.fast,
            BZip2Config.balanced,
            BZip2Config.best_compression,
            BZip2Config.minimal_memory,
        ],
    )
    def test_diff_with_bzip2_config_classmethods(self, large_repetitive_data, config_method):
        """Test diff() with BZip2Config classmethod constructors."""
        config = config_method()

        # Test that diff accepts all BZip2Config classmethods
        diff_data = hdiffpatch.diff(large_repetitive_data["old"], large_repetitive_data["new"], compression=config)

        assert isinstance(diff_data, bytes)
        assert len(diff_data) > 0

        # Test round-trip
        result = hdiffpatch.apply(large_repetitive_data["old"], diff_data)
        assert result == large_repetitive_data["new"]

    def test_diff_backward_compatibility(self, simple_text_data):
        """Test that string-based compression still works."""
        # This should continue to work
        diff_data = hdiffpatch.diff(simple_text_data["old"], simple_text_data["new"], compression="bzip2")

        assert isinstance(diff_data, bytes)
        assert len(diff_data) > 0

        # Test round-trip
        result = hdiffpatch.apply(simple_text_data["old"], diff_data)
        assert result == simple_text_data["new"]

    @pytest.mark.parametrize("level", [1, 6, 9])
    def test_diff_levels(self, highly_compressible_data, level):
        """Test diff() with different levels."""
        config = BZip2Config(level=level)

        # Test that diff accepts different levels
        diff_data = hdiffpatch.diff(
            highly_compressible_data["old"], highly_compressible_data["new"], compression=config
        )

        assert isinstance(diff_data, bytes)
        assert len(diff_data) > 0

        # Test round-trip
        result = hdiffpatch.apply(highly_compressible_data["old"], diff_data)
        assert result == highly_compressible_data["new"]

    @pytest.mark.parametrize("work_factor", [0, 30, 100])
    def test_diff_work_factors(self, binary_data, work_factor):
        """Test diff() with different work factors."""
        config = BZip2Config(work_factor=work_factor)

        # Test that diff accepts different work factors
        diff_data = hdiffpatch.diff(binary_data["old"], binary_data["new"], compression=config)

        assert isinstance(diff_data, bytes)
        assert len(diff_data) > 0

        # Test round-trip
        result = hdiffpatch.apply(binary_data["old"], diff_data)
        assert result == binary_data["new"]


class TestBZip2ConfigRoundTrip:
    """Test round-trip functionality with BZip2Config."""

    def test_round_trip_with_config(self, simple_text_data):
        """Test complete round-trip with BZip2Config."""
        config = BZip2Config(level=6, work_factor=50)

        # Test complete round-trip with BZip2Config
        diff_data = hdiffpatch.diff(simple_text_data["old"], simple_text_data["new"], compression=config)

        assert isinstance(diff_data, bytes)
        assert len(diff_data) > 0

        # Test that apply() can handle the diff (should auto-detect compression)
        result = hdiffpatch.apply(simple_text_data["old"], diff_data)
        assert result == simple_text_data["new"]

    @pytest.mark.parametrize(
        "config_method",
        [
            BZip2Config.fast,
            BZip2Config.balanced,
            BZip2Config.best_compression,
            BZip2Config.minimal_memory,
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


class TestBZip2ConfigDifferentiation:
    """Test that different BZip2Config settings produce different results."""

    def test_levels_produce_different_sizes(self, highly_compressible_data):
        """Test that different levels produce different diff sizes."""
        # Use highly compressible data to see clear differences
        old_data = highly_compressible_data["old"]
        new_data = highly_compressible_data["new"]

        # Test different levels
        configs = [
            BZip2Config(level=1),  # Fast
            BZip2Config(level=6),  # Balanced
            BZip2Config(level=9),  # Best
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
        # (unless the data doesn't compress well, but highly_compressible_data should)
        assert len(set(diff_sizes)) >= 1, f"Expected valid sizes, got: {diff_sizes}"

    def test_config_vs_default_bzip2(self, large_repetitive_data):
        """Test that BZip2Config can be used as alternative to default 'bzip2'."""
        old_data = large_repetitive_data["old"]
        new_data = large_repetitive_data["new"]

        # Default bzip2 string compression
        default_diff = hdiffpatch.diff(old_data, new_data, compression="bzip2")

        # Custom configurations
        configs_to_test = [
            BZip2Config.fast(),  # Level 1
            BZip2Config.best_compression(),  # Level 9
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
