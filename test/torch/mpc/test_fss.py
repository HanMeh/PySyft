import pytest
import torch as th
import numpy as np

from syft.frameworks.torch.mpc.fss import DPF, DIF, N

# NOTE: the FSS class is also tested in the Sycret package


@pytest.mark.parametrize("op", ["eq", "le"])
def test_fss_class(op):
    class_ = {"eq": DPF, "le": DIF}[op]
    th_op = {"eq": np.equal, "le": np.less_equal}[op]
    gather_op = {"eq": "__add__", "le": "__add__"}[op]

    # single value
    keys_a, keys_b = class_.keygen(n_values=1)

    # NOTE: The mask is added by the Rust keygen
    alpha_a = np.frombuffer(np.ascontiguousarray(keys_a[1:, 0:N]), dtype=np.uint32).astype(
        np.uint64
    )
    alpha_b = np.frombuffer(np.ascontiguousarray(keys_b[1:, 0:N]), dtype=np.uint32).astype(
        np.uint64
    )

    x = np.array([0])
    x_masked = (x + alpha_a + alpha_b).astype(np.uint64)
    y0 = class_.eval(0, x_masked, keys_a)
    y1 = class_.eval(1, x_masked, keys_b)

    assert (getattr(y0, gather_op)(y1) == th_op(x, 0)).all()

    # 1D tensor
    keys_a, keys_b = class_.keygen(n_values=3)
    alpha_a = np.frombuffer(np.ascontiguousarray(keys_a[1:, 0:N]), dtype=np.uint32).astype(
        np.uint64
    )
    alpha_b = np.frombuffer(np.ascontiguousarray(keys_b[1:, 0:N]), dtype=np.uint32).astype(
        np.uint64
    )
    x = np.array([0, 2, -2])
    x_masked = (x + alpha_a + alpha_b).astype(np.uint64)
    y0 = class_.eval(0, x_masked, keys_a)
    y1 = class_.eval(1, x_masked, keys_b)

    assert (getattr(y0, gather_op)(y1) == th_op(x, 0)).all()

    # 2D tensor
    keys_a, keys_b = class_.keygen(n_values=4)
    alpha_a = np.frombuffer(np.ascontiguousarray(keys_a[1:, 0:N]), dtype=np.uint32).astype(
        np.uint64
    )
    alpha_b = np.frombuffer(np.ascontiguousarray(keys_b[1:, 0:N]), dtype=np.uint32).astype(
        np.uint64
    )

    x = np.array([[0, 2], [-2, 0]])
    x_masked = (x + alpha_a.reshape(x.shape) + alpha_b.reshape(x.shape)).astype(np.uint64)
    y0 = class_.eval(0, x_masked, keys_a)
    y1 = class_.eval(1, x_masked, keys_b)

    assert (getattr(y0, gather_op)(y1) == th_op(x, 0)).all()

    # 3D tensor
    keys_a, keys_b = class_.keygen(n_values=8)
    alpha_a = np.frombuffer(np.ascontiguousarray(keys_a[1:, 0:N]), dtype=np.uint32).astype(
        np.uint64
    )
    alpha_b = np.frombuffer(np.ascontiguousarray(keys_b[1:, 0:N]), dtype=np.uint32).astype(
        np.uint64
    )
    x = np.array([[[0, 2], [-2, 0]], [[0, 2], [-2, 0]]])
    x_masked = (x + alpha_a.reshape(x.shape) + alpha_b.reshape(x.shape)).astype(np.uint64)
    y0 = class_.eval(0, x_masked, keys_a)
    y1 = class_.eval(1, x_masked, keys_b)

    assert (getattr(y0, gather_op)(y1) == th_op(x, 0)).all()


@pytest.mark.parametrize("op", ["eq", "le"])
def test_torch_to_numpy(op):
    class_ = {"eq": DPF, "le": DIF}[op]
    th_op = {"eq": th.eq, "le": th.le}[op]
    gather_op = {"eq": "__add__", "le": "__add__"}[op]

    # 1D tensor
    keys_a, keys_b = class_.keygen(n_values=3)

    alpha_a = np.frombuffer(np.ascontiguousarray(keys_a[1:, 0:N]), dtype=np.uint32).astype(
        np.uint64
    )
    alpha_b = np.frombuffer(np.ascontiguousarray(keys_b[1:, 0:N]), dtype=np.uint32).astype(
        np.uint64
    )

    x = th.IntTensor([0, 2, -2])
    np_x = x.numpy()
    x_masked = (np_x + alpha_a + alpha_b).astype(np.uint64)

    y0 = class_.eval(0, x_masked, keys_a)
    y1 = class_.eval(1, x_masked, keys_b)

    np_result = getattr(y0, gather_op)(y1)
    th_result = th.native_tensor(np_result)

    assert (th_result == th_op(x, 0)).all()


@pytest.mark.parametrize("op", ["eq", "le"])
def test_using_crypto_store(workers, op):
    alice, bob, me = workers["alice"], workers["bob"], workers["me"]
    class_ = {"eq": DPF, "le": DIF}[op]
    th_op = {"eq": th.eq, "le": th.le}[op]
    gather_op = {"eq": "__add__", "le": "__add__"}[op]
    primitive = {"eq": "fss_eq", "le": "fss_comp"}[op]

    me.crypto_store.provide_primitives(primitive, [alice, bob], n_instances=6)
    keys_a = alice.crypto_store.get_keys(primitive, 3, remove=True)
    keys_b = bob.crypto_store.get_keys(primitive, 3, remove=True)

    alpha_a = np.frombuffer(np.ascontiguousarray(keys_a[1:, 0:N]), dtype=np.uint32).astype(
        np.uint64
    )
    alpha_b = np.frombuffer(np.ascontiguousarray(keys_b[1:, 0:N]), dtype=np.uint32).astype(
        np.uint64
    )

    x = th.IntTensor([0, 2, -2])
    np_x = x.numpy()
    x_masked = (np_x + alpha_a + alpha_b).astype(np.uint64)

    y0 = class_.eval(0, x_masked, keys_a)
    y1 = class_.eval(1, x_masked, keys_b)

    np_result = getattr(y0, gather_op)(y1)
    th_result = th.native_tensor(np_result)

    assert (th_result == th_op(x, 0)).all()
