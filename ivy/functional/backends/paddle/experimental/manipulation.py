from typing import Optional, Union, Sequence, Tuple, NamedTuple, List
from numbers import Number
from .. import backend_version
from ivy.func_wrapper import with_unsupported_dtypes, with_unsupported_device_and_dtypes
import paddle
from ivy.utils.exceptions import IvyNotImplementedException
import ivy


@with_unsupported_dtypes(
    {"2.4.2 and below": ("int8", "int16", "uint8", "uint16")},
    backend_version,
)
def moveaxis(
    a: paddle.Tensor,
    source: Union[int, Sequence[int]],
    destination: Union[int, Sequence[int]],
    /,
    *,
    copy: Optional[bool] = None,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    return paddle.moveaxis(a, source, destination)


@with_unsupported_dtypes(
    {
        "2.4.2 and below": (
            "int8",
            "int16",
            "uint8",
            "uint16",
            "bfloat16",
            "float16",
            "complex64",
            "complex128",
            "bool",
        )
    },
    backend_version,
)
def heaviside(
    x1: paddle.Tensor,
    x2: paddle.Tensor,
    /,
    *,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    return paddle.heaviside(x1, x2)


def flipud(
    m: paddle.Tensor,
    /,
    *,
    copy: Optional[bool] = None,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    raise IvyNotImplementedException()


@with_unsupported_dtypes(
    {"2.4.2 and below": ("int16", "uint16", "bfloat16", "float16")},
    backend_version,
)
def vstack(
    arrays: Sequence[paddle.Tensor],
    /,
    *,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    dtypes = set(map(lambda x: x.dtype, arrays))
    if len(dtypes) == 1:
        dtype = dtypes.pop()
    elif len(dtypes) == 2:
        dtype = paddle.promote_types(*dtypes)
    else:
        raise ValueError("Cannot promote more than 2 dtypes per stack.")

    if dtype == paddle.bool:
        int_tensors = [paddle.cast(t, "int32") for t in arrays]
        if arrays[0].dim() >= 2:
            concat_int_tensor = paddle.concat(arrays, axis=0)
        else:
            concat_int_tensor = paddle.stack(int_tensors, axis=0)
        concat_bool_tensor = paddle.cast(concat_int_tensor, "bool")
        return concat_bool_tensor

    if arrays[0].dim() >= 2:
        return paddle.concat(arrays, axis=0).astype(dtype)
    else:
        return paddle.concat([paddle.unsqueeze(t, 0) for t in arrays], axis=0)


@with_unsupported_dtypes(
    {"2.4.2 and below": ("uint16", "bfloat16")},
    backend_version,
)
def hstack(
    arrays: Sequence[paddle.Tensor],
    /,
    *,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    dtypes = set(map(lambda x: x.dtype, arrays))
    if len(dtypes) == 1:
        dtype = dtypes.pop()
    elif len(dtypes) == 2:
        dtype = ivy.promote_types(*dtypes)
    else:
        raise ValueError("Cannot promote more than 2 dtypes per stack.")

    if arrays[0].dim() > 2:
        return paddle.concat(arrays, axis=1).astype(dtype)
    else:
        return paddle.concat(arrays, axis=-1).astype(dtype)


def rot90(
    m: paddle.Tensor,
    /,
    *,
    copy: Optional[bool] = None,
    k: Optional[int] = 1,
    axes: Optional[Tuple[int, int]] = (0, 1),
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    raise IvyNotImplementedException()


@with_unsupported_dtypes(
    {"2.4.2 and below": ("uint16", "bfloat16", "complex64", "complex128", "bool")},
    backend_version,
)
def top_k(
    x: paddle.Tensor,
    k: int,
    /,
    *,
    axis: Optional[int] = -1,
    largest: Optional[bool] = True,
    out: Optional[Tuple[paddle.Tensor, paddle.Tensor]] = None,
) -> Tuple[paddle.Tensor, paddle.Tensor]:
    topk_res = NamedTuple(
        "top_k", [("values", paddle.Tensor), ("indices", paddle.Tensor)]
    )
    val, indices = paddle.topk(x, k, axis=axis, largest=largest)
    return topk_res(val, indices)


@with_unsupported_device_and_dtypes(
    {
        "2.4.2 and below": {
            "cpu": ("int8", "int16", "uint8", "uint16", "bfloat16", "float16")
        }
    },
    backend_version,
)
def fliplr(
    m: paddle.Tensor,
    /,
    *,
    copy: Optional[bool] = None,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    return paddle.flip(m, axis=1)


def i0(
    x: paddle.Tensor,
    /,
    *,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    raise IvyNotImplementedException()


def flatten(
    x: paddle.Tensor,
    /,
    *,
    copy: Optional[bool] = None,
    start_dim: Optional[int] = 0,
    end_dim: Optional[int] = -1,
    order: Optional[str] = "C",
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    ivy.utils.assertions.check_elem_in_list(order, ["C", "F"])
    if order == "F":
        return ivy.functional.experimental.flatten(
            x, start_dim=start_dim, end_dim=end_dim, order=order
        )
    return paddle.flatten(x, start_axis=start_dim, stop_axis=end_dim)


def vsplit(
    ary: paddle.Tensor,
    indices_or_sections: Union[int, Tuple[int, ...]],
    /,
) -> List[paddle.Tensor]:
    raise IvyNotImplementedException()


def dsplit(
    ary: paddle.Tensor,
    indices_or_sections: Union[int, Tuple[int, ...]],
    /,
    *,
    copy: Optional[bool] = None,
) -> List[paddle.Tensor]:
    raise IvyNotImplementedException()


def atleast_1d(
    *arys: paddle.Tensor, copy: Optional[bool] = None
) -> List[paddle.Tensor]:
    res = []
    for ary in arys:
        ary = ivy.array(ary, copy=copy).data
        if ary.ndim < 1:
            with ivy.ArrayMode(False):
                res.append(ivy.expand_dims(ary, axis=0))
        else:
            res.append(ary)
    if len(res) == 1:
        return res[0]
    return res


def dstack(
    arrays: Sequence[paddle.Tensor],
    /,
    *,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    raise IvyNotImplementedException()


def atleast_2d(
    *arys: paddle.Tensor, copy: Optional[bool] = None
) -> List[paddle.Tensor]:
    res = []
    for ary in arys:
        ary = ivy.array(ary, copy=copy).data
        if ary.ndim < 2:
            with ivy.ArrayMode(False):
                res.append(ivy.expand_dims(ary, axis=list(range(2 - ary.ndim))))
        else:
            res.append(ary)
    if len(res) == 1:
        return res[0]
    return res


def atleast_3d(
    *arys: Union[paddle.Tensor, bool, Number], copy: Optional[bool] = None
) -> List[paddle.Tensor]:
    res = []
    for ary in arys:
        ary = ivy.array(ary, copy=copy).data
        if ary.ndim < 3:
            with ivy.ArrayMode(False):
                res.append(ivy.expand_dims(ary, axis=list(range(3 - ary.ndim))))
        else:
            res.append(ary)
    if len(res) == 1:
        return res[0]
    return res


def take_along_axis(
    arr: paddle.Tensor,
    indices: paddle.Tensor,
    axis: int,
    /,
    *,
    mode: str = "fill",
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    if arr.ndim != indices.ndim:
        raise ivy.utils.exceptions.IvyException(
            "arr and indices must have the same number of dimensions;"
            + f" got {arr.ndim} vs {indices.ndim}"
        )
    indices = indices.cast("int64")
    if mode not in ["clip", "fill", "drop"]:
        raise ValueError(
            f"Invalid mode '{mode}'. Valid modes are 'clip', 'fill', 'drop'."
        )
    arr_shape = arr.shape
    if axis < 0:
        axis += arr.ndim
    if mode == "clip":
        max_index = arr.shape[axis] - 1
        with ivy.ArrayMode(False):
            indices = ivy.clip(indices, 0, max_index)
    elif mode == "fill" or mode == "drop":
        if "float" in str(arr.dtype):
            fill_value = float("nan")
        elif "uint" in str(arr.dtype):
            fill_value = paddle.iinfo(arr.dtype).max
        else:
            fill_value = -paddle.iinfo(arr.dtype).max - 1
        with ivy.ArrayMode(False):
            indices = ivy.where(
                (indices < 0) | (indices >= arr.shape[axis]), -1, indices
            )
            arr_shape = list(arr_shape)
            arr_shape[axis] = 1
            fill_arr = ivy.full(arr_shape, fill_value, dtype=arr.dtype)
            arr = ivy.concat([arr, fill_arr], axis=axis)
            indices = ivy.where(indices < 0, arr.shape[axis] + indices, indices)

    if arr.dtype in [
        paddle.int8,
        paddle.int16,
        paddle.uint8,
        paddle.float16,
        paddle.complex64,
        paddle.complex128,
        paddle.bool,
    ]:
        if paddle.is_complex(arr):
            return paddle.complex(
                paddle.take_along_axis(arr.real(), indices, axis),
                paddle.take_along_axis(arr.imag(), indices, axis),
            )
        return paddle.take_along_axis(arr.cast("float32"), indices, axis).cast(
            arr.dtype
        )
    return paddle.take_along_axis(arr, indices, axis)


def hsplit(
    ary: paddle.Tensor,
    indices_or_sections: Union[int, Tuple[int, ...]],
    /,
    *,
    copy: Optional[bool] = None,
) -> List[paddle.Tensor]:
    raise IvyNotImplementedException()


def broadcast_shapes(*shapes: Union[List[int], List[Tuple]]) -> Tuple[int]:
    def _broadcast_shape(s1, s2):
        len_1 = len(s1)
        len_2 = len(s2)
        if len_1 == 0:
            return () if len_2 == 0 else s2
        elif len_1 != 0 and len_2 == 0:
            return s1
        else:
            return paddle.broadcast_shape(s1, s2)

    if len(shapes) == 0:
        raise ValueError("shapes=[] must be non-empty")
    elif len(shapes) == 1:
        return shapes[0]
    result = _broadcast_shape(shapes[0], shapes[1])
    for i in range(2, len(shapes)):
        result = _broadcast_shape(result, shapes[i])

    return result


@with_unsupported_device_and_dtypes(
    {"2.4.2 and below": {"cpu": ("uint16", "bfloat16")}}, backend_version
)
def expand(
    x: paddle.Tensor,
    shape: Union[List[int], List[Tuple]],
    /,
    *,
    copy: Optional[bool] = None,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    shape = list(shape)

    for i, dim in enumerate(shape):
        if dim < 0:
            shape[i] = x.shape[i]
    if x.ndim == 0:
        if len(shape) == 0:
            return x
        else:
            x = ivy.expand_dims(x, 0)
    if x.ndim > len(shape):
        x = x.reshape([-1])

    if x.dtype in [
        paddle.int8,
        paddle.int16,
        paddle.uint8,
        paddle.float16,
    ]:
        return paddle.expand(x.cast("float32"), shape).cast(x.dtype)

    elif x.dtype in [paddle.complex64, paddle.complex128]:
        x_real = paddle.expand(ivy.real(x).data, shape)
        x_imag = paddle.expand(ivy.imag(x).data, shape)
        return x_real + 1j * x_imag
    else:
        return paddle.expand(x, shape)


def concat_from_sequence(
    input_sequence: Union[Tuple[paddle.Tensor], List[paddle.Tensor]],
    /,
    *,
    new_axis: int = 0,
    axis: int = 0,
    out: Optional[paddle.Tensor] = None,
) -> paddle.Tensor:
    is_tuple = type(input_sequence) is tuple
    if is_tuple:
        input_sequence = list(input_sequence)
    if new_axis == 0:
        ret = paddle.concat(input_sequence, axis=axis)
        return ret
    elif new_axis == 1:
        ret = paddle.stack(input_sequence, axis=axis)
        return ret
