from sdf_timing.core.model import DelayPaths, Values


class TestValuesAdd:
    def test_add_full(self) -> None:
        result = Values(1, 2, 3) + Values(4, 5, 6)
        assert result == Values(5, 7, 9)

    def test_add_partial_none(self) -> None:
        result = Values(1, None, 3) + Values(4, 5, None)
        assert result == Values(5, None, None)

    def test_add_all_none(self) -> None:
        result = Values() + Values()
        assert result == Values()


class TestValuesSub:
    def test_sub_full(self) -> None:
        result = Values(5, 7, 9) - Values(4, 5, 6)
        assert result == Values(1, 2, 3)

    def test_sub_partial_none(self) -> None:
        result = Values(5, None, 9) - Values(4, 5, None)
        assert result == Values(1, None, None)


class TestValuesNeg:
    def test_neg_full(self) -> None:
        result = -Values(1, 2, 3)
        assert result == Values(-1, -2, -3)

    def test_neg_with_none(self) -> None:
        result = -Values(1, None, 3)
        assert result == Values(-1, None, -3)

    def test_neg_all_none(self) -> None:
        result = -Values()
        assert result == Values()


class TestValuesMul:
    def test_mul_scalar(self) -> None:
        result = Values(1, 2, 3) * 2
        assert result == Values(2, 4, 6)

    def test_rmul_scalar(self) -> None:
        result = 2 * Values(1, 2, 3)
        assert result == Values(2, 4, 6)

    def test_mul_with_none(self) -> None:
        result = Values(1, None, 3) * 2
        assert result == Values(2, None, 6)


class TestValuesApproxEq:
    def test_exact_equal(self) -> None:
        assert Values(1, 2, 3).approx_eq(Values(1, 2, 3))

    def test_within_tolerance(self) -> None:
        assert Values(1.0, 2.0, 3.0).approx_eq(Values(1.0 + 1e-10, 2.0, 3.0))

    def test_outside_tolerance(self) -> None:
        assert not Values(1, 2, 3).approx_eq(Values(1.1, 2, 3))

    def test_both_none_equal(self) -> None:
        assert Values().approx_eq(Values())

    def test_one_none_not_equal(self) -> None:
        assert not Values(1, None, 3).approx_eq(Values(1, 2, 3))

    def test_custom_tolerance(self) -> None:
        assert Values(1.0, 2.0, 3.0).approx_eq(Values(1.05, 2.0, 3.0), tolerance=0.1)
        assert not Values(1.0, 2.0, 3.0).approx_eq(
            Values(1.05, 2.0, 3.0), tolerance=0.01
        )


class TestValuesHash:
    def test_hash_equal(self) -> None:
        assert hash(Values(1, 2, 3)) == hash(Values(1, 2, 3))

    def test_in_set(self) -> None:
        s = {Values(1, 2, 3), Values(4, 5, 6)}
        assert Values(1, 2, 3) in s
        assert Values(4, 5, 6) in s
        assert Values(7, 8, 9) not in s


class TestDelayPathsAdd:
    def test_add_nominal(self) -> None:
        a = DelayPaths(nominal=Values(1, 2, 3))
        b = DelayPaths(nominal=Values(4, 5, 6))
        result = a + b
        assert result.nominal == Values(5, 7, 9)

    def test_add_mixed_fields(self) -> None:
        a = DelayPaths(nominal=Values(1, 2, 3), fast=Values(0.5, 1.0, 1.5))
        b = DelayPaths(nominal=Values(4, 5, 6), slow=Values(2.0, 3.0, 4.0))
        result = a + b
        assert result.nominal == Values(5, 7, 9)
        assert result.fast is None
        assert result.slow is None


class TestDelayPathsSub:
    def test_sub_nominal(self) -> None:
        a = DelayPaths(nominal=Values(5, 7, 9))
        b = DelayPaths(nominal=Values(4, 5, 6))
        result = a - b
        assert result.nominal == Values(1, 2, 3)


class TestDelayPathsApproxEq:
    def test_approx_eq_same(self) -> None:
        a = DelayPaths(nominal=Values(1, 2, 3), fast=Values(0.5, 1.0, 1.5))
        b = DelayPaths(nominal=Values(1, 2, 3), fast=Values(0.5, 1.0, 1.5))
        assert a.approx_eq(b)

    def test_approx_eq_one_none_field(self) -> None:
        a = DelayPaths(nominal=Values(1, 2, 3), fast=Values(0.5, 1.0, 1.5))
        b = DelayPaths(nominal=Values(1, 2, 3))
        assert not a.approx_eq(b)


class TestRoundTrip:
    def test_add_sub_roundtrip(self) -> None:
        a = Values(1.5, 2.7, 3.9)
        b = Values(4.1, 5.3, 6.8)
        result = a + b - b
        assert result.approx_eq(a)

    def test_delaypaths_add_sub_roundtrip(self) -> None:
        a = DelayPaths(
            nominal=Values(1.5, 2.7, 3.9),
            fast=Values(0.5, 1.0, 1.5),
            slow=Values(2.0, 3.0, 4.0),
        )
        b = DelayPaths(
            nominal=Values(4.1, 5.3, 6.8),
            fast=Values(1.0, 2.0, 3.0),
            slow=Values(0.5, 1.0, 1.5),
        )
        result = a + b - b
        assert result.approx_eq(a)
