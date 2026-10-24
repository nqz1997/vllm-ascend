# SPDX-License-Identifier: Apache-2.0
"""Contract tests for the INT2 shared import hub (ctx).

Pins the facade surface: every exported name resolves, the config instance is
a per-process singleton, the cross-module diag registry exists, and the
registry holds no tensors while diagnostics are off.

The PACKAGE-LEVEL audit tests (no star imports anywhere in the backend, the
handoff names never accessed via bare globals(), every remaining globals()
name module-local, every module's _R2XX_G binding IS the ctx dict) live in
tests/ut/oscar/test_int2_assembly.py instead: those invariants span every
backend module and are only assertable — and only meaningful — on a tree
that contains the whole backend package, which first exists at the assembly
unit.
"""
import vllm_ascend.attention.int2.ctx as ctx


def test_all_names_resolve():
    for name in ctx.__all__:
        assert hasattr(ctx, name), f"__all__ names {name!r} missing on module"


def test_oscar_cfg_is_singleton():
    import vllm_ascend.attention.int2.ctx as ctx2
    assert ctx is ctx2
    assert ctx._OSCAR_CFG is not None


def test_diag_registry_shared_dict():
    assert isinstance(ctx._R2XX_G, dict)
    ctx._R2XX_G.setdefault("_TEST_K", [0])
    ctx._R2XX_G["_TEST_K"][0] += 1
    assert ctx._R2XX_G["_TEST_K"] == [1]
    del ctx._R2XX_G["_TEST_K"]


def test_registry_holds_no_tensors_when_diagnostics_off():
    import torch
    for v in ctx._R2XX_G.values():
        assert not isinstance(v, torch.Tensor)
        if isinstance(v, (list, tuple)):
            assert not any(isinstance(e, torch.Tensor) for e in v)
        if isinstance(v, dict):
            assert not any(isinstance(e, torch.Tensor) for e in v.values())
