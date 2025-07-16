"""Tests for ZlibConfig class and zlib compression configuration."""

import pytest

import hdiffpatch
from hdiffpatch import ZlibConfig, ZlibStrategy


class TestZlibConfigClass:
    """Test ZlibConfig class functionality."""

    def test_default_construction(self):
        """Test default ZlibConfig construction."""
        config = ZlibConfig()
        assert config.level == 9
        assert config.memory_level == 8
        assert config.window == 15
        assert config.strategy == ZlibStrategy.DEFAULT
        assert config.save_window_bits is True

    def test_custom_construction(self):
        """Test ZlibConfig construction with custom parameters."""
        config = ZlibConfig(level=6, memory_level=4, window=12, strategy=ZlibStrategy.RLE, save_window_bits=False)
        assert config.level == 6
        assert config.memory_level == 4
        assert config.window == 12
        assert config.strategy == ZlibStrategy.RLE
        assert config.save_window_bits is False

    @pytest.mark.parametrize(
        "string_val,enum_val",
        [
            ("default", ZlibStrategy.DEFAULT),
            ("filtered", ZlibStrategy.FILTERED),
            ("huffman_only", ZlibStrategy.HUFFMAN_ONLY),
            ("rle", ZlibStrategy.RLE),
            ("fixed", ZlibStrategy.FIXED),
        ],
    )
    def test_strategy_string_conversion(self, string_val, enum_val):
        """Test strategy parameter accepts strings."""
        config = ZlibConfig(strategy=string_val)
        assert config.strategy == enum_val

        # Test uppercase/mixed case
        config = ZlibConfig(strategy=string_val.upper())
        assert config.strategy == enum_val

    @pytest.mark.parametrize("strategy", list(ZlibStrategy))
    def test_strategy_enum_conversion(self, strategy):
        """Test strategy parameter accepts enum values."""
        config = ZlibConfig(strategy=strategy)
        assert config.strategy == strategy

    @pytest.mark.parametrize("value", [True, 1, "true", [1, 2, 3]])
    def test_save_window_bits_truthy_conversion(self, value):
        """Test save_window_bits parameter converts truthy values to True."""
        config = ZlibConfig(save_window_bits=value)
        assert config.save_window_bits is True

    @pytest.mark.parametrize("value", [False, 0, "", None, []])
    def test_save_window_bits_falsy_conversion(self, value):
        """Test save_window_bits parameter converts falsy values to False."""
        config = ZlibConfig(save_window_bits=value)
        assert config.save_window_bits is False


class TestZlibConfigValidation:
    """Test ZlibConfig parameter validation."""

    @pytest.mark.parametrize("level", range(10))  # 0-9
    def test_level_valid_values(self, level):
        """Test level accepts valid values."""
        config = ZlibConfig(level=level)
        assert config.level == level

    @pytest.mark.parametrize("level", [-1, 10])
    def test_level_invalid_range(self, level):
        """Test level rejects out-of-range values."""
        with pytest.raises(ValueError, match="'level' must be"):
            ZlibConfig(level=level)

    @pytest.mark.parametrize("level", ["6", 6.5])
    def test_level_invalid_type(self, level):
        """Test level rejects invalid types."""
        with pytest.raises(TypeError, match="'level' must be <class 'int'>"):
            ZlibConfig(level=level)  # type: ignore[arg-type]

    @pytest.mark.parametrize("level", range(1, 10))  # 1-9
    def test_memory_level_valid_values(self, level):
        """Test memory level accepts valid values."""
        config = ZlibConfig(memory_level=level)
        assert config.memory_level == level

    @pytest.mark.parametrize("level", [0, 10])
    def test_memory_level_invalid_range(self, level):
        """Test memory level rejects out-of-range values."""
        with pytest.raises(ValueError, match="'memory_level' must be"):
            ZlibConfig(memory_level=level)

    def test_memory_level_invalid_type(self):
        """Test memory level rejects invalid types."""
        with pytest.raises(TypeError, match="'memory_level' must be <class 'int'>"):
            ZlibConfig(memory_level="8")  # type: ignore[arg-type]

    @pytest.mark.parametrize("bits", range(9, 16))  # 9-15
    def test_window_valid_values(self, bits):
        """Test window bits accepts valid values."""
        config = ZlibConfig(window=bits)
        assert config.window == bits

    @pytest.mark.parametrize("bits", [8, 16])
    def test_window_invalid_range(self, bits):
        """Test window bits rejects out-of-range values."""
        with pytest.raises(ValueError, match="'window' must be"):
            ZlibConfig(window=bits)

    def test_window_invalid_type(self):
        """Test window bits rejects invalid types."""
        with pytest.raises(TypeError, match="'window' must be <class 'int'>"):
            ZlibConfig(window="15")  # type: ignore[arg-type]

    def test_strategy_invalid_string(self):
        """Test strategy rejects invalid string values."""
        with pytest.raises(ValueError, match="Invalid strategy 'invalid'"):
            ZlibConfig(strategy="invalid")

    @pytest.mark.parametrize("strategy", [123, None])
    def test_strategy_invalid_type(self, strategy):
        """Test strategy rejects invalid types."""
        with pytest.raises(TypeError, match="strategy must be a ZlibStrategy enum or string"):
            ZlibConfig(strategy=strategy)  # type: ignore[arg-type]


class TestZlibConfigClassmethods:
    """Test ZlibConfig classmethod constructors."""

    @pytest.mark.parametrize(
        "method_name,expected_attrs",
        [
            (
                "fast",
                {
                    "level": 1,
                    "memory_level": 1,
                    "window": 9,
                    "strategy": ZlibStrategy.DEFAULT,
                    "save_window_bits": True,
                },
            ),
            (
                "balanced",
                {
                    "level": 6,
                    "memory_level": 8,
                    "window": 15,
                    "strategy": ZlibStrategy.DEFAULT,
                    "save_window_bits": True,
                },
            ),
            (
                "best_compression",
                {
                    "level": 9,
                    "memory_level": 9,
                    "window": 15,
                    "strategy": ZlibStrategy.DEFAULT,
                    "save_window_bits": True,
                },
            ),
            (
                "minimal_memory",
                {
                    "level": 6,
                    "memory_level": 1,
                    "window": 9,
                    "strategy": ZlibStrategy.DEFAULT,
                    "save_window_bits": True,
                },
            ),
            (
                "png_optimized",
                {
                    "level": 9,
                    "memory_level": 8,
                    "window": 15,
                    "strategy": ZlibStrategy.RLE,
                    "save_window_bits": True,
                },
            ),
        ],
    )
    def test_classmethod_configs(self, method_name, expected_attrs):
        """Test ZlibConfig classmethod constructors."""
        config = getattr(ZlibConfig, method_name)()
        for attr_name, expected_value in expected_attrs.items():
            assert getattr(config, attr_name) == expected_value


class TestZlibConfigMethods:
    """Test ZlibConfig instance methods."""

    def test_hashability(self):
        """Test that ZlibConfig objects are hashable."""
        config1 = ZlibConfig(level=6, strategy=ZlibStrategy.RLE)
        config2 = ZlibConfig(level=6, strategy=ZlibStrategy.RLE)
        config3 = ZlibConfig(level=9, strategy=ZlibStrategy.RLE)

        # Test that equal objects have same hash
        assert hash(config1) == hash(config2)

        # Test that different objects have different hashes (usually)
        assert hash(config1) != hash(config3)

        # Test that objects can be used in sets and as dict keys
        config_set = {config1, config2, config3}
        assert len(config_set) == 2  # config1 and config2 are the same

        config_dict = {config1: "value1", config3: "value3"}
        assert len(config_dict) == 2


class TestZlibConfigIntegration:
    """Test ZlibConfig integration with hdiffpatch.diff() function."""

    def test_diff_with_zlib_config_basic(self, simple_text_data):
        """Test diff() function accepts ZlibConfig objects."""
        config = ZlibConfig(level=6)

        # Test that diff accepts ZlibConfig objects
        diff_data = hdiffpatch.diff(simple_text_data["old"], simple_text_data["new"], compression=config)

        assert isinstance(diff_data, bytes)
        assert len(diff_data) > 0

        # Test round-trip
        result = hdiffpatch.apply(simple_text_data["old"], diff_data)
        assert result == simple_text_data["new"]

    @pytest.mark.parametrize(
        "config_method",
        [
            ZlibConfig.fast,
            ZlibConfig.balanced,
            ZlibConfig.best_compression,
            ZlibConfig.minimal_memory,
            ZlibConfig.png_optimized,
        ],
    )
    def test_diff_with_zlib_config_classmethods(self, large_repetitive_data, config_method):
        """Test diff() with ZlibConfig classmethod constructors."""
        config = config_method()

        # Test that diff accepts all ZlibConfig classmethods
        diff_data = hdiffpatch.diff(large_repetitive_data["old"], large_repetitive_data["new"], compression=config)

        assert isinstance(diff_data, bytes)
        assert len(diff_data) > 0

        # Test round-trip
        result = hdiffpatch.apply(large_repetitive_data["old"], diff_data)
        assert result == large_repetitive_data["new"]

    def test_diff_backward_compatibility(self, simple_text_data):
        """Test that string-based compression still works."""
        # This should continue to work
        diff_data = hdiffpatch.diff(simple_text_data["old"], simple_text_data["new"], compression="zlib")

        assert isinstance(diff_data, bytes)
        assert len(diff_data) > 0

        # Test round-trip
        result = hdiffpatch.apply(simple_text_data["old"], diff_data)
        assert result == simple_text_data["new"]

    @pytest.mark.parametrize("level", [1, 6, 9])
    def test_diff_levels(self, highly_compressible_data, level):
        """Test diff() with different levels."""
        config = ZlibConfig(level=level)

        # Test that diff accepts different levels
        diff_data = hdiffpatch.diff(
            highly_compressible_data["old"], highly_compressible_data["new"], compression=config
        )

        assert isinstance(diff_data, bytes)
        assert len(diff_data) > 0

        # Test round-trip
        result = hdiffpatch.apply(highly_compressible_data["old"], diff_data)
        assert result == highly_compressible_data["new"]

    @pytest.mark.parametrize("strategy", list(ZlibStrategy))
    def test_diff_compression_strategies(self, binary_data, strategy):
        """Test diff() with different compression strategies."""
        config = ZlibConfig(strategy=strategy)

        # Test that diff accepts different compression strategies
        diff_data = hdiffpatch.diff(binary_data["old"], binary_data["new"], compression=config)

        assert isinstance(diff_data, bytes)
        assert len(diff_data) > 0

        # Test round-trip
        result = hdiffpatch.apply(binary_data["old"], diff_data)
        assert result == binary_data["new"]

    @pytest.mark.parametrize(
        "config_method",
        [
            ZlibConfig.minimal_memory,
            ZlibConfig.best_compression,
        ],
    )
    def test_diff_memory_configurations(self, large_repetitive_data, config_method):
        """Test diff() with different memory configurations."""
        config = config_method()

        # Test that diff accepts different memory configurations
        diff_data = hdiffpatch.diff(large_repetitive_data["old"], large_repetitive_data["new"], compression=config)

        assert isinstance(diff_data, bytes)
        assert len(diff_data) > 0

        # Test round-trip
        result = hdiffpatch.apply(large_repetitive_data["old"], diff_data)
        assert result == large_repetitive_data["new"]


class TestZlibConfigRoundTrip:
    """Test round-trip functionality with ZlibConfig."""

    def test_round_trip_with_config(self, simple_text_data):
        """Test complete round-trip with ZlibConfig."""
        config = ZlibConfig(level=6, strategy=ZlibStrategy.RLE)

        # Test complete round-trip with ZlibConfig
        diff_data = hdiffpatch.diff(simple_text_data["old"], simple_text_data["new"], compression=config)

        assert isinstance(diff_data, bytes)
        assert len(diff_data) > 0

        # Test that apply() can handle the diff (should auto-detect compression)
        result = hdiffpatch.apply(simple_text_data["old"], diff_data)
        assert result == simple_text_data["new"]

    @pytest.mark.parametrize(
        "config_method",
        [
            ZlibConfig.fast,
            ZlibConfig.balanced,
            ZlibConfig.best_compression,
            ZlibConfig.minimal_memory,
            ZlibConfig.png_optimized,
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


class TestZlibConfigEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_data_with_config(self, empty_data):
        """Test ZlibConfig with empty data."""
        config = ZlibConfig.fast()

        # Test ZlibConfig with empty data
        diff_data = hdiffpatch.diff(empty_data["old"], empty_data["new"], compression=config)

        assert isinstance(diff_data, bytes)
        assert len(diff_data) > 0

        # Test round-trip
        result = hdiffpatch.apply(empty_data["old"], diff_data)
        assert result == empty_data["new"]

    def test_identical_data_with_config(self, identical_data):
        """Test ZlibConfig with identical data."""
        config = ZlibConfig.best_compression()

        # Test ZlibConfig with identical data
        diff_data = hdiffpatch.diff(identical_data["old"], identical_data["new"], compression=config)

        assert isinstance(diff_data, bytes)
        assert len(diff_data) > 0

        # Test round-trip
        result = hdiffpatch.apply(identical_data["old"], diff_data)
        assert result == identical_data["new"]

    def test_large_data_with_minimal_memory(self, random_data):
        """Test minimal memory config with large data."""
        config = ZlibConfig.minimal_memory()

        # Test minimal memory config with large data
        diff_data = hdiffpatch.diff(random_data["old"], random_data["new"], compression=config)

        assert isinstance(diff_data, bytes)
        assert len(diff_data) > 0

        # Test round-trip
        result = hdiffpatch.apply(random_data["old"], diff_data)
        assert result == random_data["new"]


class TestZlibConfigDifferentiation:
    """Test that different ZlibConfig settings produce different results."""

    def test_levels_produce_different_sizes(self, highly_compressible_data):
        """Test that different levels produce different diff sizes."""
        # Use highly compressible data to see clear differences
        old_data = highly_compressible_data["old"]
        new_data = highly_compressible_data["new"]

        # Test different levels
        configs = [
            ZlibConfig(level=1),  # Fast
            ZlibConfig(level=6),  # Balanced
            ZlibConfig(level=9),  # Best
        ]

        diff_sizes = []
        for config in configs:
            diff_data = hdiffpatch.diff(old_data, new_data, compression=config)
            diff_sizes.append(len(diff_data))

            # Ensure round-trip works
            result = hdiffpatch.apply(old_data, diff_data)
            assert result == new_data

        # Generally, higher compression levels should produce smaller or equal sizes
        # (though this isn't always guaranteed due to compression overhead)
        level1_size, level6_size, level9_size = diff_sizes

        # All sizes should be positive
        assert all(size > 0 for size in diff_sizes)

        # At minimum, we should see that not all sizes are identical
        # (unless the data doesn't compress well, but highly_compressible_data should)
        assert len(set(diff_sizes)) >= 2, f"Expected different sizes, got: {diff_sizes}"

    def test_strategies_produce_different_sizes(self, large_repetitive_data):
        """Test that different compression strategies produce different diff sizes."""
        old_data = large_repetitive_data["old"]
        new_data = large_repetitive_data["new"]

        # Test strategies that should behave differently on repetitive data
        strategies = [
            ZlibStrategy.DEFAULT,
            ZlibStrategy.RLE,  # Should be good for repetitive data
            ZlibStrategy.HUFFMAN_ONLY,  # Should be different from RLE
        ]

        diff_sizes = []
        for strategy in strategies:
            config = ZlibConfig(level=9, strategy=strategy)
            diff_data = hdiffpatch.diff(old_data, new_data, compression=config)
            diff_sizes.append(len(diff_data))

            # Ensure round-trip works
            result = hdiffpatch.apply(old_data, diff_data)
            assert result == new_data

        # All sizes should be positive
        assert all(size > 0 for size in diff_sizes)

        # Different strategies should produce different results
        # (at least some of them should be different)
        assert len(set(diff_sizes)) >= 2, f"Expected different sizes for strategies, got: {diff_sizes}"

    @pytest.mark.parametrize("mem_level", [1, 4, 8, 9])
    def test_memory_levels_maintain_functionality(self, mem_level):
        """Test that different memory levels work correctly."""
        # Create data that might show memory level differences
        old_data = b"ABCD" * 500  # Repetitive pattern
        new_data = b"EFGH" * 500  # Different pattern, same structure

        config = ZlibConfig(level=9, memory_level=mem_level)
        diff_data = hdiffpatch.diff(old_data, new_data, compression=config)

        # Ensure round-trip works
        result = hdiffpatch.apply(old_data, diff_data)
        assert result == new_data

        # Size should be positive
        assert len(diff_data) > 0

    @pytest.mark.parametrize("window", [9, 12, 15])
    def test_window_functionality(self, window):
        """Test that different window bits work correctly."""
        # Create data to test window sizes
        pattern = b"The quick brown fox jumps over the lazy dog. "
        old_data = pattern * 100  # ~4.5KB
        new_data = pattern.replace(b"brown", b"black") * 100

        config = ZlibConfig(level=9, window=window)
        diff_data = hdiffpatch.diff(old_data, new_data, compression=config)

        # Ensure round-trip works
        result = hdiffpatch.apply(old_data, diff_data)
        assert result == new_data

        # Size should be positive
        assert len(diff_data) > 0

    def test_config_vs_default_zlib(self, large_repetitive_data):
        """Test that ZlibConfig produces different results than default 'zlib'."""
        old_data = large_repetitive_data["old"]
        new_data = large_repetitive_data["new"]

        # Default zlib string compression
        default_diff = hdiffpatch.diff(old_data, new_data, compression="zlib")

        # Custom configurations that should differ from default
        configs_to_test = [
            ZlibConfig.fast(),  # Level 1 vs default level 9
            ZlibConfig(level=9, strategy=ZlibStrategy.RLE),  # Different strategy
            ZlibConfig(level=9, window=12),  # Smaller window
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

        # At least one config should produce a different size than default
        different_sizes = [size for size in config_sizes if size != default_size]
        assert len(different_sizes) > 0, (
            f"Expected some configs to differ from default size {default_size}, got: {config_sizes}"
        )
