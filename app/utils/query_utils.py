from typing import List, Any, Tuple
from http import HTTPStatus
from flask import request, abort
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select, asc, desc, and_, or_
from app.extensions import db
from app.models.common import PaginationMeta


class FilterSpec(BaseModel):
    """Represents a single filter specification"""
    field: str = Field(..., description="Field name to filter on")
    op: str = Field(default="==", description="Filter operator")
    value: Any = Field(default=None, description="Filter value")


class SortSpec(BaseModel):
    """Represents a single sort specification"""
    field: str = Field(..., description="Field name to sort by")
    direction: str = Field(default="asc", description="Sort direction (asc/desc)")


def parse_pagination_from_request() -> PaginationMeta:
    """Parse pagination parameters from request query string."""
    try:
        page_raw = request.args.get("page")
        size_raw = request.args.get("size")

        page = None
        size = None

        if page_raw is not None:
            try:
                page = int(page_raw)
                if page < 1:
                    abort(HTTPStatus.BAD_REQUEST, description="Page number must be greater than 0")
            except ValueError:
                abort(HTTPStatus.BAD_REQUEST,
                      description=f"Invalid page parameter: '{page_raw}' is not a valid integer")

        if size_raw is not None:
            try:
                size = int(size_raw)
                if size < 1:
                    abort(HTTPStatus.BAD_REQUEST, description="Page size must be greater than 0")
                if size > 100:
                    abort(HTTPStatus.BAD_REQUEST, description="Page size cannot exceed 100")
            except ValueError:
                abort(HTTPStatus.BAD_REQUEST,
                      description=f"Invalid size parameter: '{size_raw}' is not a valid integer")

        params = {}
        if page is not None:
            params["page"] = page
        if size is not None:
            params["size"] = size

        return PaginationMeta(**params)

    except ValidationError as err:
        error_details = []
        for error in err.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            message = error["message"]
            error_details.append(f"{field}: {message}")
        abort(HTTPStatus.BAD_REQUEST, description=f"Invalid pagination: {'; '.join(error_details)}")


def normalize_operator(op: str) -> str:
    """Convert user-friendly operators to standard format"""
    operator_mapping = {
        'eq': '==',
        'ne': '!=',
        'gt': '>',
        'gte': '>=',
        'ge': '>=',
        'lt': '<',
        'lte': '<=',
        'le': '<=',
        '==': '==',
        '!=': '!=',
        '>': '>',
        '>=': '>=',
        '<': '<',
        '<=': '<=',
        'like': 'like',
        'ilike': 'ilike',
        'in': 'in',
        'not_in': 'not_in',
        'is_null': 'is_null',
        'is_not_null': 'is_not_null'
    }

    normalized = operator_mapping.get(op.lower())
    if normalized is None:
        abort(HTTPStatus.BAD_REQUEST,
              description=f"Unsupported operator '{op}'. Supported operators: {', '.join(operator_mapping.keys())}")

    return normalized


def parse_filters_from_request(allowed_fields: List[str] = None) -> List[FilterSpec]:
    """Parse filter parameters from request query string."""
    filters = []

    for key, value in request.args.items():
        if key in ['sort', 'page', 'size']:
            continue

        # Handle simple format: field=value or field__op=value
        if '__' in key:
            field, op = key.split('__', 1)
        else:
            field = key
            op = '=='

        # Handle complex format: filter[field][op]=value
        if key.startswith('filter[') and key.endswith(']'):
            try:
                inner = key[7:-1]  # Remove 'filter[' and ']'
                if '][' in inner:
                    field, op = inner.split('][', 1)
                else:
                    field = inner
                    op = '=='
            except ValueError:
                abort(HTTPStatus.BAD_REQUEST, description=f"Invalid filter format: {key}")
        elif key.startswith('filter['):
            continue  # Skip malformed filter parameters

        # Skip if not in the above formats
        if key.startswith('filter[') and not key.endswith(']'):
            continue

        # Validate allowed fields
        if allowed_fields and field not in allowed_fields:
            abort(HTTPStatus.BAD_REQUEST,
                  description=f"Filtering on field '{field}' is not allowed. "
                              f"Allowed fields: {', '.join(allowed_fields)}")

        # Parse value for special operators
        if op in ['in', 'not_in']:
            filter_value = value.split(',') if value else []
        elif op in ['is_null', 'is_not_null']:
            filter_value = None
        else:
            filter_value = value

        try:
            filters.append(FilterSpec(field=field, op=normalize_operator(op), value=filter_value))
        except ValidationError as e:
            abort(HTTPStatus.BAD_REQUEST,
                  description=f"Invalid filter parameter '{key}': {str(e)}")

    return filters


def parse_sorts_from_request(allowed_fields: List[str] = None) -> List[SortSpec]:
    """Parse sort parameters from request query string."""
    sorts = []

    # Handle simple format: sort=field1,-field2,field3
    sort_param = request.args.get('sort')
    if sort_param:
        for sort_field in sort_param.split(','):
            sort_field = sort_field.strip()
            if sort_field.startswith('-'):
                field = sort_field[1:]
                direction = 'desc'
            else:
                field = sort_field
                direction = 'asc'

            # Validate allowed fields
            if allowed_fields and field not in allowed_fields:
                abort(HTTPStatus.BAD_REQUEST,
                      description=f"Sorting on field '{field}' is not allowed. "
                                  f"Allowed fields: {', '.join(allowed_fields)}")

            try:
                sorts.append(SortSpec(field=field, direction=direction))
            except ValidationError as e:
                abort(HTTPStatus.BAD_REQUEST,
                      description=f"Invalid sort parameter '{sort_field}': {str(e)}")

    # Handle complex format: sort[field]=direction
    for key, value in request.args.items():
        if key.startswith('sort[') and key.endswith(']'):
            field = key[5:-1]  # Remove 'sort[' and ']'

            # Validate allowed fields
            if allowed_fields and field not in allowed_fields:
                abort(HTTPStatus.BAD_REQUEST,
                      description=f"Sorting on field '{field}' is not allowed. "
                                  f"Allowed fields: {', '.join(allowed_fields)}")

            if value.lower() not in ['asc', 'desc']:
                abort(HTTPStatus.BAD_REQUEST,
                      description=f"Invalid sort direction '{value}'. Must be 'asc' or 'desc'")

            try:
                sorts.append(SortSpec(field=field, direction=value.lower()))
            except ValidationError as e:
                abort(HTTPStatus.BAD_REQUEST,
                      description=f"Invalid sort parameter '{key}': {str(e)}")

    return sorts


def apply_filters_to_select(select_stmt, filters: List[FilterSpec], model_class):
    """Apply filters to a SQLAlchemy 2.0 select statement"""
    if not filters:
        return select_stmt

    conditions = []

    for filter_spec in filters:
        # Get the model attribute
        if not hasattr(model_class, filter_spec.field):
            abort(HTTPStatus.BAD_REQUEST,
                  description=f"Field '{filter_spec.field}' does not exist on model")

        field_attr = getattr(model_class, filter_spec.field)
        value = filter_spec.value

        # Apply operator
        try:
            if filter_spec.op == '==':
                condition = field_attr == value
            elif filter_spec.op == '!=':
                condition = field_attr != value
            elif filter_spec.op == '>':
                condition = field_attr > value
            elif filter_spec.op == '>=':
                condition = field_attr >= value
            elif filter_spec.op == '<':
                condition = field_attr < value
            elif filter_spec.op == '<=':
                condition = field_attr <= value
            elif filter_spec.op == 'like':
                condition = field_attr.like(f"%{value}%")
            elif filter_spec.op == 'ilike':
                condition = field_attr.ilike(f"%{value}%")
            elif filter_spec.op == 'in':
                condition = field_attr.in_(value)
            elif filter_spec.op == 'not_in':
                condition = ~field_attr.in_(value)
            elif filter_spec.op == 'is_null':
                condition = field_attr.is_(None)
            elif filter_spec.op == 'is_not_null':
                condition = field_attr.is_not(None)
            else:
                abort(HTTPStatus.BAD_REQUEST,
                      description=f"Unsupported operator: {filter_spec.op}")

            conditions.append(condition)

        except Exception as e:
            abort(HTTPStatus.BAD_REQUEST,
                  description=f"Error applying filter {filter_spec.field} {filter_spec.op} {value}: {str(e)}")

    # Combine all conditions with AND
    if conditions:
        select_stmt = select_stmt.where(and_(*conditions))

    return select_stmt


def apply_sorts_to_select(select_stmt, sorts: List[SortSpec], model_class):
    """Apply sorting to a SQLAlchemy 2.0 select statement"""
    if not sorts:
        return select_stmt

    order_by_clauses = []

    for sort_spec in sorts:
        # Get the model attribute
        if not hasattr(model_class, sort_spec.field):
            abort(HTTPStatus.BAD_REQUEST,
                  description=f"Field '{sort_spec.field}' does not exist on model")

        field_attr = getattr(model_class, sort_spec.field)

        # Apply sort direction
        if sort_spec.direction == 'asc':
            order_by_clauses.append(asc(field_attr))
        else:
            order_by_clauses.append(desc(field_attr))

    if order_by_clauses:
        select_stmt = select_stmt.order_by(*order_by_clauses)

    return select_stmt


def apply_query_filters_sorts_pagination(model_class,
                                         allowed_filter_fields: List[str] = None,
                                         allowed_sort_fields: List[str] = None) -> Tuple[List[Any], PaginationMeta]:
    """
    Apply filters, sorting, and pagination using SQLAlchemy 2.0+ and Flask-SQLAlchemy 3.0+

    Args:
        model_class: SQLAlchemy model class (e.g., Item)
        allowed_filter_fields: List of field names that can be filtered on
        allowed_sort_fields: List of field names that can be sorted on

    Returns:
        Tuple of (result_items, pagination_metadata)
    """
    # Parse request parameters
    filters = parse_filters_from_request(allowed_filter_fields)
    sorts = parse_sorts_from_request(allowed_sort_fields)
    pagination_params = parse_pagination_from_request()

    # Create base select statement
    select_stmt = select(model_class)

    # Apply filters
    select_stmt = apply_filters_to_select(select_stmt, filters, model_class)

    # Apply sorting
    select_stmt = apply_sorts_to_select(select_stmt, sorts, model_class)

    # Apply pagination using Flask-SQLAlchemy 3.0+
    try:
        pagination = db.paginate(
            select_stmt,
            page=pagination_params.page,
            per_page=pagination_params.size,
            error_out=False
        )

        # Create pagination metadata in your expected format
        pagination_meta = PaginationMeta(
            page=pagination.page,
            size=pagination.per_page,
            page_count=pagination.pages,
            total_count=pagination.total,
            has_next=pagination.has_next,
            has_prev=pagination.has_prev
        )

        return pagination.items, pagination_meta

    except Exception as err:
        abort(HTTPStatus.INTERNAL_SERVER_ERROR, description=f"Database query error: {str(err)}")
