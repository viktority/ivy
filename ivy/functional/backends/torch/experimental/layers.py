# global
from typing import Optional, Union, Tuple, Literal, Sequence
import torch
import math

# local
import ivy
from ivy.func_wrapper import with_unsupported_dtypes, handle_mixed_function
from . import backend_version
from ivy.functional.ivy.layers import _handle_padding, _get_num_padded_values
from ivy.functional.ivy.experimental.layers import _padding_ceil_mode


@with_unsupported_dtypes({"1.11.0 and below": ("bfloat16", "float16")}, backend_version)
def max_pool1d(
    x: torch.Tensor,
    kernel: Union[int, Tuple[int]],
    strides: Union[int, Tuple[int]],
    padding: str,
    /,
    *,
    data_format: str = "NWC",
    out: Optional[torch.Tensor] = None,
) -> torch.Tensor:
    if isinstance(strides, int):
        strides = (strides,)
    elif len(strides) == 1:
        strides = (strides[0],)

    if isinstance(kernel, int):
        kernel = (kernel,)
    elif len(kernel) == 1:
        kernel = (kernel[0],)

    if data_format == "NWC":
        x = x.permute((0, 2, 1))
    x_shape = x.shape[2]
    pad_w = _handle_padding(x_shape, strides[0], kernel[0], padding)
    x = torch.nn.functional.pad(
        x, [pad_w // 2, pad_w - pad_w // 2], value=float("-inf")
    )

    res = torch.nn.functional.max_pool1d(x, kernel, strides, 0)

    if data_format == "NWC":
        res = res.permute((0, 2, 1))
    return res


@with_unsupported_dtypes(
    {
        "1.11.0 and below": (
            "float16",
            "bfloat16",
        )
    },
    backend_version,
)
def max_pool2d(
    x: torch.Tensor,
    kernel: Union[int, Tuple[int], Tuple[int, int]],
    strides: Union[int, Tuple[int], Tuple[int, int]],
    padding: Union[str, int, Tuple[int], Tuple[int, int]],
    /,
    *,
    data_format: str = "NHWC",
    dilation: Union[int, Tuple[int], Tuple[int, int]] = 1,
    ceil_mode: bool = False,
    out: Optional[torch.Tensor] = None,
) -> torch.Tensor:
    if isinstance(strides, int):
        strides = (strides, strides)
    elif len(strides) == 1:
        strides = (strides[0], strides[0])

    if isinstance(kernel, int):
        kernel = (kernel, kernel)
    elif len(kernel) == 1:
        kernel = (kernel[0], kernel[0])

    if isinstance(dilation, int):
        dilation = (dilation, dilation)
    elif len(dilation) == 1:
        dilation = (dilation[0], dilation[0])

    if isinstance(padding, int):
        padding = [(padding,) * 2] * 2
    elif isinstance(padding, tuple) and len(padding) == 1:
        padding = [(padding[0],) * 2] * 2
    elif isinstance(padding, tuple) and len(padding) == 2:
        padding = [(padding[0],) * 2, (padding[1],) * 2]

    if isinstance(padding, (tuple, list)):
        ivy.utils.assertions.check_kernel_padding_size(kernel, padding)

    if data_format == "NHWC":
        x = x.permute(0, 3, 1, 2)
    x_shape = list(x.shape[2:])

    new_kernel = [kernel[i] + (kernel[i] - 1) * (dilation[i] - 1) for i in range(2)]

    if isinstance(padding, str):
        pad_h = _handle_padding(x_shape[0], strides[0], new_kernel[0], padding)
        pad_w = _handle_padding(x_shape[1], strides[1], new_kernel[1], padding)
        pad_list = [pad_w // 2, pad_w - pad_w // 2, pad_h // 2, pad_h - pad_h // 2]
    else:
        # torch pad takes width padding first, then height padding
        padding = (padding[1], padding[0])
        pad_list = [item for sublist in padding for item in sublist]

    x = torch.nn.functional.pad(
        x,
        pad_list,
        value=float("-inf"),
    )

    res = torch.nn.functional.max_pool2d(x, kernel, strides, 0, dilation, ceil_mode)
    if data_format == "NHWC":
        return res.permute(0, 2, 3, 1)
    return res


@with_unsupported_dtypes(
    {
        "1.11.0 and below": (
            "float16",
            "bfloat16",
        )
    },
    backend_version,
)
def max_pool3d(
    x: torch.Tensor,
    kernel: Union[int, Tuple[int], Tuple[int, int, int]],
    strides: Union[int, Tuple[int], Tuple[int, int, int]],
    padding: str,
    /,
    *,
    data_format: str = "NDHWC",
    out: Optional[torch.Tensor] = None,
) -> torch.Tensor:
    if isinstance(strides, int):
        strides = (strides, strides, strides)
    elif len(strides) == 1:
        strides = (strides[0], strides[0], strides[0])
    if isinstance(kernel, int):
        kernel = (kernel, kernel, kernel)
    elif len(kernel) == 1:
        kernel = (kernel[0], kernel[0], kernel[0])
    if data_format == "NDHWC":
        x = x.permute(0, 4, 1, 2, 3)
    x_shape = list(x.shape[2:])
    pad_d = _handle_padding(x_shape[0], strides[0], kernel[0], padding)
    pad_h = _handle_padding(x_shape[1], strides[1], kernel[1], padding)
    pad_w = _handle_padding(x_shape[2], strides[2], kernel[2], padding)
    x = torch.nn.functional.pad(
        x,
        [
            pad_w // 2,
            pad_w - pad_w // 2,
            pad_h // 2,
            pad_h - pad_h // 2,
            pad_d // 2,
            pad_d - pad_d // 2,
        ],
        value=float("-inf"),
    )
    if padding != "VALID" and padding != "SAME":
        raise ivy.utils.exceptions.IvyException(
            "Invalid padding arg {}\n"
            'Must be one of: "VALID" or "SAME"'.format(padding)
        )
    res = torch.nn.functional.max_pool3d(x, kernel, strides, 0)
    if data_format == "NDHWC":
        res = res.permute(0, 2, 3, 4, 1)
    return res


def _add_ceil_pad_to_pad_list(num_pad, k, c):
    return num_pad + (num_pad - ((k * num_pad) / (k - c)))


def _get_specific_pad(x_shape, kernel, strides, padding, dims):
    if isinstance(padding, str):
        if padding == "SAME":
            pad_specific = [
                _handle_padding(x_shape[i], strides[i], kernel[i], padding)
                for i in range(dims - 1, -1, -1)
            ]
            pad_list_top = [pad_specific[i] // 2 for i in range(dims)]
            pad_list_bot = [pad_specific[i] - pad_specific[i] // 2 for i in range(dims)]
            padding = [None] * len(pad_list_top) * 2
            padding[::2] = pad_list_top
            padding[1::2] = pad_list_bot
            pad_specific = pad_specific[::-1]
        else:
            pad_specific = [0] * dims
            padding = [0] * dims * 2
    else:
        if isinstance(padding, int):
            padding = [(padding, padding)] * dims
        pad_specific = [sum(padding[i]) for i in range(dims)]
        padding = [item for sublist in padding for item in sublist[::-1]][::-1]
    return padding, pad_specific


@with_unsupported_dtypes({"1.11.0 and below": ("bfloat16", "float16")}, backend_version)
def avg_pool1d(
    x: torch.Tensor,
    kernel: Union[int, Tuple[int]],
    strides: Union[int, Tuple[int]],
    padding: str,
    /,
    *,
    data_format: str = "NWC",
    count_include_pad: bool = False,
    ceil_mode: bool = False,
    out: Optional[torch.Tensor] = None,
) -> torch.Tensor:
    if isinstance(strides, int):
        strides = (strides,)
    elif len(strides) == 1:
        strides = (strides[0],)

    if isinstance(kernel, int):
        kernel = (kernel,)
    elif len(kernel) == 1:
        kernel = (kernel[0],)

    if data_format == "NWC":
        x = x.permute(0, 2, 1)
    x_shape = x.shape[2]
    if isinstance(padding, str):
        pad_specific = [
            _handle_padding(x_shape, strides[i], kernel[i], padding) for i in range(1)
        ]
        padding = [
            (pad_specific[i] // 2, pad_specific[i] - pad_specific[i] // 2)
            for i in range(1)
        ]
    else:
        pad_specific = [sum(padding[i]) for i in range(1)]
    x = torch.nn.functional.pad(x, *padding, value=0.0)

    res = torch.nn.functional.avg_pool1d(x, kernel, strides, 0, ceil_mode)

    if not count_include_pad and any(pad_specific):
        num_padded_values = ivy.map(
            _get_num_padded_values,
            constant={
                "p": pad_specific[0],
                "n": x_shape,
                "k": kernel[0],
                "s": strides[0],
            },
            unique={
                "i": torch.arange(res.shape[2]),
            },
        )
        num_padded_values = torch.tensor(num_padded_values, dtype=res.dtype)

        if ceil_mode:
            _, c = _padding_ceil_mode(x_shape, kernel[0], padding[0], strides[0], True)
            num_padded_values[-1] = _add_ceil_pad_to_pad_list(
                num_padded_values[-1], kernel[0], c
            )

        res = (kernel[0] * res) / (kernel[0] - num_padded_values)

    if data_format == "NWC":
        res = res.permute(0, 2, 1)
    return res


def _adjust_num_padded_values_to_ceil(
    pad_specific, num_padded_values, x_shape, kernel, strides, dims
):
    for i in range(dims):
        pad = [pad_specific[i] // 2, pad_specific[i] - pad_specific[i] // 2]
        _, c = _padding_ceil_mode(x_shape[i], kernel[i], pad, strides[i], True)
        num_padded_values[i][-1] = _add_ceil_pad_to_pad_list(
            num_padded_values[i][-1], kernel[i], c
        )
    return num_padded_values


@with_unsupported_dtypes(
    {
        "1.11.0 and below": (
            "float16",
            "bfloat16",
        )
    },
    backend_version,
)
def avg_pool2d(
    x: torch.Tensor,
    kernel: Union[int, Tuple[int], Tuple[int, int]],
    strides: Union[int, Tuple[int], Tuple[int, int]],
    padding: str,
    /,
    *,
    data_format: str = "NHWC",
    count_include_pad: bool = False,
    ceil_mode: bool = False,
    out: Optional[torch.Tensor] = None,
) -> torch.Tensor:
    if isinstance(strides, int):
        strides = (strides, strides)
    elif len(strides) == 1:
        strides = (strides[0], strides[0])

    if isinstance(kernel, int):
        kernel = (kernel, kernel)
    elif len(strides) == 1:
        kernel = (kernel[0], kernel[0])

    if data_format == "NHWC":
        x = x.permute(0, 3, 1, 2)
    x_shape = list(x.shape[2:])
    padding, pad_specific = _get_specific_pad(x_shape, kernel, strides, padding, 2)
    x = torch.nn.functional.pad(
        x,
        padding,
        value=0.0,
    )
    res = torch.nn.functional.avg_pool2d(x, kernel, strides, 0, ceil_mode)

    if not count_include_pad and any(pad_specific):
        num_padded_values = [
            ivy.map(
                _get_num_padded_values,
                constant={
                    "p": pad_specific[i],
                    "n": x_shape[i],
                    "k": kernel[i],
                    "s": strides[i],
                },
                unique={
                    "i": torch.arange(res.shape[i + 2]),
                },
            )
            for i in range(2)
        ]

        if ceil_mode:
            for i in range(2):
                num_padded_values = _adjust_num_padded_values_to_ceil(
                    pad_specific, num_padded_values, x_shape, kernel, strides, 2
                )

        num_padded_values1 = torch.tensor(num_padded_values[0], dtype=res.dtype)[
            :, None
        ]
        num_padded_values2 = torch.tensor(num_padded_values[1], dtype=res.dtype)[
            None, :
        ]
        num_padded_values = (
            num_padded_values1 * kernel[1]
            + num_padded_values2 * kernel[0]
            - num_padded_values1 * num_padded_values2
        )
        res = (kernel[0] * kernel[1] * res) / (
            kernel[0] * kernel[1] - num_padded_values
        )
    if data_format == "NHWC":
        return res.permute(0, 2, 3, 1)
    return res


@with_unsupported_dtypes(
    {
        "1.11.0 and below": (
            "float16",
            "bfloat16",
        )
    },
    backend_version,
)
def avg_pool3d(
    x: torch.Tensor,
    kernel: Union[int, Tuple[int], Tuple[int, int, int]],
    strides: Union[int, Tuple[int], Tuple[int, int, int]],
    padding: str,
    /,
    *,
    data_format: str = "NDHWC",
    count_include_pad: bool = False,
    ceil_mode: bool = False,
    out: Optional[torch.Tensor] = None,
) -> torch.Tensor:
    if isinstance(strides, int):
        strides = (strides, strides, strides)
    elif len(strides) == 1:
        strides = (strides[0], strides[0], strides[0])
    if isinstance(kernel, int):
        kernel = (kernel, kernel, kernel)
    elif len(kernel) == 1:
        kernel = (kernel[0], kernel[0], kernel[0])
    if data_format == "NDHWC":
        x = x.permute(0, 4, 1, 2, 3)
    x_shape = list(x.shape[2:])
    padding, pad_specific = _get_specific_pad(x_shape, kernel, strides, padding, 3)
    x = torch.nn.functional.pad(
        x,
        padding,
        value=0.0,
    )
    res = torch.nn.functional.avg_pool3d(x, kernel, strides, 0)

    if not count_include_pad and any(pad_specific):
        num_padded_values = [
            torch.tensor(
                ivy.map(
                    _get_num_padded_values,
                    constant={
                        "p": pad_specific[i],
                        "n": x_shape[i],
                        "k": kernel[i],
                        "s": strides[i],
                    },
                    unique={
                        "i": torch.arange(res.shape[i + 2]),
                    },
                ),
                dtype=res.dtype,
            )
            for i in range(3)
        ]

        if ceil_mode:
            for i in range(3):
                num_padded_values = _adjust_num_padded_values_to_ceil(
                    pad_specific, num_padded_values, x_shape, kernel, strides, 3
                )
        num_padded_values1 = num_padded_values[0].reshape((-1, 1, 1))
        num_padded_values2 = num_padded_values[1].reshape((1, -1, 1))
        num_padded_values3 = num_padded_values[2].reshape((1, 1, -1))
        num_padded_values = (
            num_padded_values1 * kernel[1] * kernel[2]
            + num_padded_values2 * kernel[0] * kernel[2]
            + num_padded_values3 * kernel[0] * kernel[1]
            + num_padded_values1 * num_padded_values2 * num_padded_values3
            - num_padded_values1 * num_padded_values2 * kernel[2]
            - num_padded_values1 * num_padded_values3 * kernel[1]
            - num_padded_values2 * num_padded_values3 * kernel[0]
        )
        kernel_mul = kernel[0] * kernel[1] * kernel[2]
        res = (kernel_mul * res) / (kernel_mul - num_padded_values)

    if data_format == "NDHWC":
        res = res.permute(0, 2, 3, 4, 1)
    return res


def dct(
    x: torch.Tensor,
    /,
    *,
    type: Literal[1, 2, 3, 4] = 2,
    n: Optional[int] = None,
    axis: int = -1,
    norm: Optional[Literal["ortho"]] = None,
    out: Optional[torch.Tensor] = None,
) -> torch.tensor:
    if norm not in (None, "ortho"):
        raise ValueError("Norm must be either None or 'ortho'")
    if x.dtype not in [torch.float32, torch.float64]:
        x = x.type(torch.float32)
    if axis < 0:
        axis = axis + len(x.shape)
    if n is not None:
        signal_len = x.shape[axis]
        if n <= signal_len:
            local_idx = [slice(None)] * len(x.shape)
            local_idx[axis] = slice(None, n)
            x = x[local_idx]
        else:
            pad_idx = [0] * 2 * len(x.shape)
            pad_idx[(len(pad_idx) - 1) - (2 * axis)] = n - signal_len
            x = torch.nn.functional.pad(x, pad_idx)
    real_zero = torch.tensor(0.0, dtype=x.dtype)
    axis_dim = x.shape[axis]
    axis_dim_float = torch.tensor(axis_dim, dtype=x.dtype)

    if type == 1:
        if norm:
            raise ValueError("Normalization not supported for type-I DCT")
        axis_idx = [slice(None)] * len(x.shape)
        axis_idx[axis] = slice(1, -1)
        x = torch.concat([x, x.flip(axis)[axis_idx]], dim=axis)
        dct_out = torch.real(torch.fft.rfft(x, dim=axis))
        return dct_out

    elif type == 2:
        scale_dims = [1] * len(x.shape)
        scale_dims[axis] = axis_dim
        scale = 2.0 * torch.exp(
            torch.complex(
                real_zero,
                -torch.arange(axis_dim_float) * math.pi * 0.5 / axis_dim_float,
            )
        ).view(scale_dims)

        axis_idx = [slice(None)] * len(x.shape)
        axis_idx[axis] = slice(None, axis_dim)
        dct_out = torch.real(
            torch.fft.rfft(x, n=2 * axis_dim, axis=axis)[axis_idx] * scale
        )
        if norm == "ortho":
            n1 = 0.5 * torch.rsqrt(axis_dim_float)
            n2 = n1 * math.sqrt(2.0)
            sf = torch.nn.functional.pad(n1.unsqueeze(0), (0, axis_dim - 1), value=n2)
            dct_out = sf.view(scale_dims) * dct_out
        return dct_out

    elif type == 3:
        scale_dims = [1] * len(x.shape)
        scale_dims[axis] = axis_dim
        scale = 2.0 * torch.exp(
            torch.complex(
                real_zero, torch.arange(axis_dim_float) * math.pi * 0.5 / axis_dim_float
            )
        ).view(scale_dims)
        if norm == "ortho":
            n1 = torch.sqrt(axis_dim_float)
            n2 = n1 * math.sqrt(0.5)
            scale_dims = [1] * len(x.shape)
            scale_dims[axis] = axis_dim
            sf = torch.nn.functional.pad(n1.unsqueeze(0), (0, axis_dim - 1), value=n2)
            x = x * sf.view(scale_dims)
        else:
            x = x * axis_dim_float

        axis_idx = [slice(None)] * len(x.shape)
        axis_idx[axis] = slice(None, axis_dim)
        dct_out = torch.real(
            torch.fft.irfft(
                scale * torch.complex(x, real_zero), n=2 * axis_dim, axis=axis
            )
        )[axis_idx]
        return dct_out

    elif type == 4:
        dct_2 = dct(x, type=2, n=2 * axis_dim, axis=axis, norm=None)
        axis_idx = [slice(None)] * len(x.shape)
        axis_idx[axis] = slice(1, None, 2)
        dct_out = dct_2[axis_idx]
        if norm == "ortho":
            dct_out *= math.sqrt(0.5) * torch.rsqrt(axis_dim_float)
        return dct_out


def fft(
    x: torch.Tensor,
    dim: int,
    /,
    *,
    norm: str = "backward",
    n: Union[int, Tuple[int]] = None,
    out: Optional[torch.Tensor] = None,
) -> torch.Tensor:
    if not isinstance(dim, int):
        raise ivy.utils.exceptions.IvyError(
            f"Expecting <class 'int'> instead of {type(dim)}"
        )
    if n is None:
        n = x.shape[dim]
    if n < -len(x.shape):
        raise ivy.utils.exceptions.IvyError(
            f"Invalid dim {dim}, expecting ranging"
            " from {-len(x.shape)} to {len(x.shape)-1}  "
        )
    if not isinstance(n, int):
        raise ivy.utils.exceptions.IvyError(
            f"Expecting <class 'int'> instead of {type(n)}"
        )
    if n <= 1:
        raise ivy.utils.exceptions.IvyError(
            f"Invalid data points {n}, expecting more than 1"
        )
    if norm != "backward" and norm != "ortho" and norm != "forward":
        raise ivy.utils.exceptions.IvyError(f"Unrecognized normalization mode {norm}")
    return torch.fft.fft(x, n, dim, norm, out=out)


def dropout1d(
    x: torch.Tensor,
    prob: float,
    /,
    *,
    training: bool = True,
    data_format: str = "NWC",
    out: Optional[torch.Tensor] = None,
) -> torch.Tensor:
    if training:
        if data_format == "NWC":
            perm = (0, 2, 1) if len(x.shape) == 3 else (1, 0)
            x = torch.permute(x, perm)
        # ToDo: switch to native dropout1d once torch version is updated.
        noise_shape = list(x.shape)
        noise_shape[-1] = 1
        mask = torch.rand(noise_shape) > prob
        res = torch.where(mask, x / (1 - prob), torch.zeros_like(x))
        if data_format == "NWC":
            res = torch.permute(res, perm)
        return res
    else:
        return x


@with_unsupported_dtypes(
    {
        "1.11.0 and below": (
            "float16",
            "bfloat16",
        )
    },
    backend_version,
)
def dropout3d(
    x: torch.Tensor,
    prob: float,
    /,
    *,
    training: bool = True,
    data_format: str = "NDHWC",
    out: Optional[torch.Tensor] = None,
) -> torch.Tensor:
    if training:
        is_batched = len(x.shape) == 5
        if data_format == "NDHWC":
            perm = (0, 4, 1, 2, 3) if is_batched else (3, 0, 1, 2)
            x = torch.permute(x, perm)
        # ToDo: switch to native dropout1d once torch version is updated.
        noise_shape = list(x.shape)
        noise_shape[-3:] = [1] * 3
        mask = torch.rand(noise_shape) > prob
        res = torch.where(mask, x / (1 - prob), torch.zeros_like(x))
        if data_format == "NDHWC":
            perm = (0, 2, 3, 4, 1) if is_batched else (1, 2, 3, 0)
            res = torch.permute(res, perm)
        return res
    else:
        return x


def ifft(
    x: torch.Tensor,
    dim: int,
    *,
    norm: str = "backward",
    n: Union[int, Tuple[int]] = None,
    out: Optional[torch.Tensor] = None,
) -> torch.Tensor:
    if not isinstance(dim, int):
        raise ivy.utils.exceptions.IvyError(
            f"Expecting <class 'int'> instead of {type(dim)}"
        )
    if n is None:
        n = x.shape[dim]
    if n < -len(x.shape):
        raise ivy.utils.exceptions.IvyError(
            f"Invalid dim {dim}, expecting ranging"
            " from {-len(x.shape)} to {len(x.shape)-1}  "
        )
    if not isinstance(n, int):
        raise ivy.utils.exceptions.IvyError(
            f"Expecting <class 'int'> instead of {type(n)}"
        )
    if n <= 1:
        raise ivy.utils.exceptions.IvyError(
            f"Invalid data points {n}, expecting more than 1"
        )
    if norm != "backward" and norm != "ortho" and norm != "forward":
        raise ivy.utils.exceptions.IvyError(f"Unrecognized normalization mode {norm}")
    return torch.fft.ifft(x, n, dim, norm, out=out).resolve_conj()


def embedding(
    weights: torch.Tensor,
    indices: torch.Tensor,
    /,
    *,
    max_norm: Optional[int] = None,
    out: Optional[torch.Tensor] = None,
) -> torch.Tensor:
    return torch.nn.functional.embedding(indices, weights, max_norm=max_norm)


embedding.support_native_out = False


@handle_mixed_function(
    lambda *args, mode="linear", **kwargs: mode
    not in [
        "tf_area",
        "bicubic_tensorflow",
        "mitchellcubic",
        "lanczos3",
        "lanczos5",
        "gaussian",
    ]
)
def interpolate(
    x: torch.Tensor,
    size: Union[Sequence[int], int],
    /,
    *,
    mode: Literal[
        "linear",
        "bilinear",
        "trilinear",
        "nearest",
        "area",
        "nearest_exact",
        "tf_area",
        "bicubic",
        "mitchellcubic",
        "lanczos3",
        "lanczos5",
        "gaussian",
    ] = "linear",
    scale_factor: Optional[Union[Sequence[int], int]] = None,
    recompute_scale_factor: Optional[bool] = None,
    align_corners: Optional[bool] = None,
    antialias: bool = False,
    out: Optional[torch.Tensor] = None,
):
    return torch.nn.functional.interpolate(
        x,
        size=size,
        mode=mode,
        align_corners=align_corners,
        antialias=antialias,
        scale_factor=scale_factor,
        recompute_scale_factor=recompute_scale_factor,
    )


@with_unsupported_dtypes({"1.11.0 and below": ("bfloat16", "float16")}, backend_version)
def adaptive_avg_pool1d(input, output_size):
    return torch.nn.functional.adaptive_avg_pool1d(input, output_size)


@with_unsupported_dtypes({"1.11.0 and below": ("bfloat16", "float16")}, backend_version)
def adaptive_avg_pool2d(input, output_size):
    return torch.nn.functional.adaptive_avg_pool2d(input, output_size)
