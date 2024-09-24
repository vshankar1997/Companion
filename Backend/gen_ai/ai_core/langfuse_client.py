from langfuse import Langfuse
import os
import traceback
import logging
from django.conf import settings


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# langfuse = Langfuse(
#     secret_key=settings.LANGFUSE_SECRET_KEY,
#     public_key=settings.LANGFUSE_PUBLIC_KEY,
#     host=settings.LANGFUSE_HOST,
# )


def log_and_raise_error(error_message, trace_id=None):
    """Logs the error and raises the exception"""
    logging.error(error_message)
    logging.error(traceback.format_exc())
    # if trace_id:
    #     langfuse.event(trace_id=trace_id, name="Error", input=error_message)
    raise Exception(error_message)
