import math

from flask import abort, Blueprint, jsonify, request
from http import HTTPStatus
from sqlalchemy.exc import SQLAlchemyError
from app.models import BaseResponse, Pagination, Item, GetItems
from app.schemas import Item as ItemsTable


items_bp = Blueprint(name="items", import_name= __name__, url_prefix="/api/v1")

@items_bp.route("/items", methods=["GET"])
def get_items():
    try:
        # todo - shouldn't we handle this in a separate function?
        # Get pagination params from query string
        page = request.args.get("page", default=1, type=int)
        size = request.args.get("size", default=10, type=int)

        DEFAULT_PAGE = 1
        DEFAULT_SIZE = 10
        MAX_SIZE = 100
        if page < 1:
            page = DEFAULT_PAGE
        if size < 1 or size > MAX_SIZE:
            size = DEFAULT_SIZE

        # Query items with pagination
        paginated_items = ItemsTable.query.paginate(page=page, per_page=size, error_out=False)

        # Convert SQLAlchemy objects to Pydantic models
        items = [Item.model_validate(item) for item in paginated_items.items]

        # Calculate pagination info
        total_count = paginated_items.total
        page_count = math.ceil(total_count / size) if total_count > 0 else 1

        pagination = Pagination(
            page=page,
            size=size,
            page_count=page_count,
            total_count=total_count,
            has_next=paginated_items.has_next,
            has_prev=paginated_items.has_prev
        )

        base_response = BaseResponse()

        response_model = GetItems(
            items=items,
            pagination=pagination,
            base_response=base_response
        )

        return jsonify(response_model.model_dump(mode="json")), HTTPStatus.OK
    # todo - use abort() to trigger the proper error handler
    except SQLAlchemyError as err:
        # Handle database errors
        base_response = BaseResponse(
            status_message=f"Database error: {str(err)}",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value  # todo - this needs to be a mapping of 1000nnn values
        )

        error_response = GetItems(
            items=[],
            pagination=Pagination(),
            base_response=base_response
        )
        return jsonify(error_response.model_dump(mode="json")), HTTPStatus.INTERNAL_SERVER_ERROR
    except Exception as err:
        # Handle other errors
        base_response = BaseResponse(
            status_message=f"An error occurred: {str(err)}",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value  # todo - this needs to be a mapping of 1000nnn values
        )

        error_response = GetItems(
            items=[],
            pagination=Pagination(),
            base_response=base_response
        )
        return jsonify(error_response.model_dump(mode="json")), HTTPStatus.INTERNAL_SERVER_ERROR