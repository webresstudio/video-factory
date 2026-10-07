"""Compatibility helpers for faster-whisper's PyAV calls.

Some faster-whisper releases pass ``metadata_errors`` to ``av.open``. PyAV
19 removed that keyword, so retry only that specific unsupported-keyword
failure without it. Other decoding errors remain untouched.
"""
from functools import wraps


def compatible_open(open_func):
    """Return an idempotent ``av.open`` wrapper tolerant of older/newer APIs."""
    if getattr(open_func, "_wvf_metadata_errors_compat", False):
        return open_func

    @wraps(open_func)
    def open_with_metadata_fallback(*args, **kwargs):
        try:
            return open_func(*args, **kwargs)
        except TypeError as exc:
            message = str(exc)
            if "metadata_errors" not in kwargs or "unexpected keyword argument" not in message:
                raise
            retry_kwargs = dict(kwargs)
            retry_kwargs.pop("metadata_errors")
            return open_func(*args, **retry_kwargs)

    open_with_metadata_fallback._wvf_metadata_errors_compat = True
    return open_with_metadata_fallback


def patch_av_open():
    """Install the narrow PyAV compatibility wrapper for this process."""
    import av

    av.open = compatible_open(av.open)
