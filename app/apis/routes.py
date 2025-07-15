from flask import abort, Blueprint, jsonify, request
from http import HTTPStatus
from app.models import BaseResponse, Item, GetItems
from app.schemas import Item as ItemsTable
from app.utils.query_utils import apply_query_filters_sorts_pagination

items_bp = Blueprint(name="items", import_name=__name__, url_prefix="/api/v1")


@items_bp.route("/items", methods=["GET"])
def get_items():
    """
    Retrieve collection of items with filtering, sorting, and pagination.
    Compatible with SQLAlchemy 2.0+ and Flask-SQLAlchemy 3.0+

    Query Parameter Examples:

    Filtering:
    - ?name=Apple
    - ?price__gte=10.50
    - ?category_id__in=1,2,3
    - ?filter[name][eq]=Apple
    - ?filter[price][gte]=10.50

    Sorting:
    - ?sort=name (ascending)
    - ?sort=-price (descending)
    - ?sort=name,-price (multiple fields)
    - ?sort[name]=asc&sort[price]=desc

    Pagination:
    - ?page=1&size=20

    Combined:
    - ?name__ilike=apple&sort=-created_at&page=1&size=10
    """

    # Define allowed fields for filtering and sorting
    allowed_filter_fields = [
        'id', 'name', 'description', 'price', 'quantity',
        'category_id', 'created_at', 'updated_at'
    ]
    allowed_sort_fields = [
        'id', 'name', 'price', 'quantity', 'category_id',
        'created_at', 'updated_at'
    ]

    # Apply filters, sorting, and pagination using SQLAlchemy 2.0+
    items_data, pagination = apply_query_filters_sorts_pagination(
        model_class=ItemsTable,
        allowed_filter_fields=allowed_filter_fields,
        allowed_sort_fields=allowed_sort_fields
    )

    # Convert SQLAlchemy objects to Pydantic models
    try:
        items = [Item.model_validate(item) for item in items_data]
    except Exception as err:
        abort(HTTPStatus.UNPROCESSABLE_ENTITY, description=f"Data validation failed: {str(err)}")

    # Create response using your existing model structure
    response_model = GetItems(
        items=items,
        pagination=pagination,
        base_response=BaseResponse()
    )

    return jsonify(response_model.model_dump(mode="json")), HTTPStatus.OK