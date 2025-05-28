import asyncio
import concurrent.futures
import logging
from typing import Callable, Any, TypeVar, Optional

T = TypeVar('T')

def execute_with_timeout(
        func: Callable[...,T],
        timeout: float,
        default_value: Optional[T] = None,
        *args: Any,
        **kwargs: Any
) -> Optional[T]:
    """
    Execute a function with a timeout. If the function does not complete within the timeout,
    it returns a default value.

    :param func: The function to execute.
    :param timeout: The timeout in seconds.
    :param default_value: The value to return if the function times out.
    :param args: Positional arguments to pass to the function.
    :param kwargs: Keyword arguments to pass to the function.
    :return: The result of the function or the default value if it times out.
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            future.cancel()
            if default_value is not None:
                return default_value
            else:
                raise TimeoutError(f"Function '{func.__name__}' timed out after {timeout} seconds.")
        except Exception as e:
            logging.error(f"Error executing function '{func.__name__}': {e}")
            raise e
        
async def execute_with_timeout_async(
    func: Callable[..., T],
    timeout: float,
    default_value: Optional[T] = None,
    *args: Any,
    **kwargs: Any
) -> Optional[T]:
    """
    Asynchronously execute a function with a timeout. If the function does not complete within the timeout,
    it returns a default value.

    :param func: The function to execute.
    :param timeout: The timeout in seconds.
    :param default_value: The value to return if the function times out.
    :param args: Positional arguments to pass to the function.
    :param kwargs: Keyword arguments to pass to the function.
    :return: The result of the function or the default value if it times out.
    """
    loop = asyncio.get_event_loop()
    try:
        # 在线程池中运行同步函数
        result = await asyncio.wait_for(
            loop.run_in_executor(None, lambda: func(*args, **kwargs)),
            timeout=timeout
        )
        return result
    except asyncio.TimeoutError:
        if default_value is not None:
            return default_value
        else:
            raise TimeoutError(f"Function '{func.__name__}' timed out after {timeout} seconds.")
    except Exception as e:
        logging.error(f"Error executing function '{func.__name__}': {e}")
        raise e