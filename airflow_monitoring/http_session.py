import requests
import structlog
from request_session import RequestSession


def get_session(user: str, psw: str, user_agent: str, logger):
    logger = logger or structlog.get_logger("http_session")
    # pylint: disable=no-member
    requests.packages.urllib3.disable_warnings(
        requests.packages.urllib3.exceptions.InsecureRequestWarning
    )
    return RequestSession(
        auth=(user, psw),
        max_retries=3,  # how many times to retry in case server error occurs
        raise_for_status=True,  # raise an exception if failed on every attempt
        verify=False,
        user_agent=user_agent,
        request_category="general",
        logger=logger,
        log_prefix="session",
    )