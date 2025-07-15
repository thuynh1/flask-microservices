import logging
from flask import jsonify, Flask, Response
from http import HTTPStatus
from werkzeug.exceptions import (NotFound, InternalServerError, BadRequest, UnprocessableEntity)
from app.models.common import BaseResponse, ErrorResponse

logger = logging.getLogger(__name__)

# todo - abstract, lots of repeated code
def handle_bad_request(error: BadRequest) -> tuple[Response, HTTPStatus]:
    """400 BAD REQUEST"""
    error_message = f"{error.description}"
    logger.error(f"{error} {error_message}")
    error_response = ErrorResponse(
        base_response=BaseResponse(
            status_message=error_message,
            status_code=100400
        )
    )

    return jsonify(error_response.model_dump(mode="json")), HTTPStatus.BAD_REQUEST

def handle_not_found(error: NotFound) -> tuple[Response, HTTPStatus]:
    """404 NOT FOUND"""
    error_message = f"{error.description}"
    logger.error(f"{error} {error_message}")
    error_response = ErrorResponse(
        base_response=BaseResponse(
            status_message=error_message,
            status_code=100404
        )
    )

    return jsonify(error_response.model_dump(mode="json")), HTTPStatus.NOT_FOUND

def handle_unprocessable_entity(error: UnprocessableEntity) -> tuple[Response, HTTPStatus]:
    """422 UNPROCESSABLE ENTITY"""
    error_message = f"{error.description}"
    logger.error(f"{error} {error_message}")
    error_response = ErrorResponse(
        base_response=BaseResponse(
            status_message=error_message,
            status_code=100422
        )
    )

def handle_internal_server_error(error: InternalServerError) -> tuple[Response, HTTPStatus]:
    """500 INTERNAL SERVER ERROR"""
    error_message = f"{error.description}"
    logger.error(f"{error} {error_message}")
    error_response = ErrorResponse(
        base_response=BaseResponse(
            status_message=error_message,
            status_code=100500
        )
    )

    return jsonify(error_response.model_dump(mode="json")), HTTPStatus.INTERNAL_SERVER_ERROR


def register_error_handlers(app: Flask) -> None:
    app.register_error_handler(HTTPStatus.BAD_REQUEST, handle_bad_request)
    app.register_error_handler(HTTPStatus.NOT_FOUND, handle_not_found)
    app.register_error_handler(HTTPStatus.UNPROCESSABLE_ENTITY, handle_unprocessable_entity)
    app.register_error_handler(HTTPStatus.INTERNAL_SERVER_ERROR, handle_internal_server_error)
