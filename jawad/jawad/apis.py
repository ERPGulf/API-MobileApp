import frappe

from werkzeug.wrappers import Response, Request
import json


@frappe.whitelist(allow_guest=True)  # pylint: disable=no-member
def categories_List():
    """
    Returns a list of all categories.
    """
    # noinspection PyUnresolvedReferences
    doc = frappe.db.get_all(  # pylint: disable=no-member
        "Item Group",
        fields=["categories.id as id", "categories.title as name"],
        filters={"name": "Products"},
    )
    for item in doc:
        if item.get("id") is not None:
            item["id"] = int(item["id"])
    return Response(json.dumps({"data": doc}), status=200, mimetype="application/json")


@frappe.whitelist(allow_guest=True)  # pylint: disable=no-member
def updated_or_newly_added_items():
    """
    Returns a list of updated or newly added products and customers since a given timestamp.
    """
    since = frappe.local.form_dict.get("updated_at")  # pylint: disable=no-member
    if not since:
        return Response(
            json.dumps({"error": "Missing required parameter 'updated_at'"}),
            status=400,
            mimetype="application/json",
        )

    items = frappe.db.get_all(  # pylint: disable=no-member
        "Item",
        fields=["item_code", "item_name as product_name", "modified as updated_at"],
        filters={"modified": [">=", since]},
    )

    customers = frappe.db.get_all(  # pylint: disable=no-member
        "Customer",
        fields=["name as id", "customer_name as name", "modified as updated_at"],
        filters={"modified": [">=", since]},
    )

    products = []
    for item in items:
        products.append(
            {
                "product_id": int(item["item_code"]),  # assuming item_code is numeric
                "product_name": item["product_name"],
                "updated_at": str(item["updated_at"]),
            }
        )

    # Build customer list
    customers_list = []
    for customer in customers:
        customers_list.append(
            {
                "id": (
                    int(customer["id"])
                    if str(customer["id"]).isdigit()
                    else customer["id"]
                ),
                "name": customer["name"],
                "updated_at": str(customer["updated_at"]),
            }
        )

    result = {
        "products": products,
        "customers": customers_list,
    }

    return Response(json.dumps(result), status=200, mimetype="application/json")


@frappe.whitelist(allow_guest=True)  # pylint: disable=no-member
def valid_promotion_list():
    """
    Returns a list of valid promotions.
    """
    promotions = frappe.get_all(  # pylint: disable=no-member
        "Promotional Scheme",
        fields=[
            "name",
            "price_discount_slabs.rate_or_discount as percentage",
            "price_discount_slabs.max_amount as value",
            "valid_from",
            "valid_upto",
        ],
        filters={"disable": 0},
    )
    for promotion in promotions:
        promotion["valid_from"] = str(promotion["valid_from"])
        promotion["valid_upto"] = str(promotion["valid_upto"])
    return Response(
        json.dumps({"data": promotions}), status=200, mimetype="application/json"
    )


@frappe.whitelist(allow_guest=True)  # pylint: disable=no-member
def customer_list():
    """
    Returns a list of all customers.
    """
    customers = frappe.get_all(  # pylint: disable=no-member
        "Customer",
        fields=[
            "name as id",
            "customer_name as name",
            "mobile_no as phone",
            "email_id as email",
        ],
    )
    return Response(
        json.dumps({"data": customers}), status=200, mimetype="application/json"
    )


@frappe.whitelist(allow_guest=True)  # pylint: disable=no-member
def create_customer(name, phone, email):
    """
    Creates a new customer with the given name, phone, and email.
    """
    if not name or not phone or not email:
        return Response(
            json.dumps({"error": "Missing required parameters: name, phone, email"}),
            status=400,
            mimetype="application/json",
        )

    customer = frappe.get_doc(  # pylint: disable=no-member
        {
            "doctype": "Customer",
            "customer_name": name,
            "mobile_no": phone,
            "email_id": email,
        }
    )
    customer.insert(ignore_permissions=True)
    return Response(
        json.dumps({"message": "Customer created successfully", "id": customer.name}),
        status=201,
        mimetype="application/json",
    )


@frappe.whitelist(allow_guest=True)  # pylint: disable=no-member
def update_customer(name, phone):
    """
    Updates an existing customer's phone number based on name.
    """
    if not name or not phone:
        return Response(
            json.dumps({"error": "Missing required parameters: name, phone"}),
            status=400,
            mimetype="application/json",
        )

    customer = frappe.get_list(  # pylint: disable=no-member
        "Customer",
        fields=["name"],
        filters={"customer_name": name},
        limit_page_length=1,
    )

    if not customer:
        return Response(
            json.dumps({"error": "Customer not found"}),
            status=404,
            mimetype="application/json",
        )

    # Get the customer's DocName (primary key)
    customer_name = customer[0]["name"]

    # Update the mobile number using frappe.db.set_value
    frappe.db.set_value(  # pylint: disable=no-member
        "Customer", customer_name, "mobile_no", phone
    )

    # Commit the transaction to save changes

    return Response(
        json.dumps({"message": "Customer phone number updated successfully"}),
        status=200,
        mimetype="application/json",
    )


@frappe.whitelist(allow_guest=True)  # pylint: disable=no-member
def parse_json_field(field):
    try:
        return json.loads(field) if isinstance(field, str) else field
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON format for field: {field}")


@frappe.whitelist(allow_guest=True)  # pylint: disable=no-member
def post_order(customer_id, branch_id, promotion_code, total):
    """Creates a new order for the given customer with the specified items."""

    if not customer_id:
        return Response(
            json.dumps({"error": "Missing required parameters: customer_id, items"}),
            status=400,
            mimetype="application/json",
        )

    try:
        items = parse_json_field(
            frappe.form_dict.get("items")  # pylint: disable=no-member
        )

        invoice_items = [
            {
                "item_code": (
                    item["product_id"]
                    if frappe.get_value(  # pylint: disable=no-member
                        "Item", {"name": item["product_id"]}, "name"
                    )
                    else None
                ),
                "qty": item.get("quantity", 0),
                "rate": item.get("price", 0),
                "delivery_date": item.get(
                    "delivery_date",
                    frappe.utils.nowdate(),  # pylint: disable=no-member
                ),
                "uom": item.get("uom", "Nos"),
                "warehouse": item.get("warehouse", "All Warehouses - erp"),
            }
            for item in items
        ]
        order = frappe.get_doc(  # pylint: disable=no-member
            {
                "doctype": "Sales Order",
                "customer": customer_id,
                "items": invoice_items,
                "coupon_code": promotion_code,
                "branch_id": branch_id,
                "total1": total,
            }
        )
        order.insert(ignore_permissions=True)
        return Response(
            json.dumps({"message": "Order created successfully", "id": order.name}),
            status=200,
            mimetype="application/json",
        )
    except Exception as e:
        return Response(
            json.dumps({"error": str(e)}),
            status=500,
            mimetype="application/json",
        )


@frappe.whitelist(allow_guest=True)  # pylint: disable=no-member
def order_list(customer_id):
    """
    Returns a list of all orders.
    """
    try:
        orders = frappe.get_all(  # pylint: disable=no-member
            "Sales Order",
            fields=[
                "name as id",
                "delivery_date as date",
                "grand_total as total",
            ],
            filters={"customer": customer_id},
            order_by="creation desc",
        )
        for order in orders:
            order["date"] = str(order["date"])
        return Response(
            json.dumps({"data": orders}), status=200, mimetype="application/json"
        )
    except Exception as e:
        return Response(
            json.dumps({"error": str(e)}),
            status=500,
            mimetype="application/json",
        )


@frappe.whitelist(allow_guest=True)  # pylint: disable=no-member
def branches_list():
    """
    Returns a list of all branches.
    """
    try:
        branches = frappe.get_all(  # pylint: disable=no-member
            "Branch",
            fields=["name as id", "branch as name", "city"],
        )
        return Response(
            json.dumps({"data": branches}), status=200, mimetype="application/json"
        )
    except Exception as e:
        return Response(
            json.dumps({"error": str(e)}),
            status=500,
            mimetype="application/json",
        )


@frappe.whitelist(allow_guest=True)  # pylint: disable=no-member
def product_list(product_id=None):
    """
    Returns product details (optionally filtered by product_id).
    """
    try:
        products = frappe.get_all(  # pylint: disable=no-member
            "Item",
            fields=["name", "item_name", "item_code", "standard_rate", "image", "sku"],
            filters={"name": product_id} if product_id else None,
        )

        product_list_data = []

        for product in products:
            # Fetch media gallery
            media_list = [
                media.get("media")
                for media in frappe.get_all(  # pylint: disable=no-member
                    "media", filters={"parent": product.name}, fields=["media"]
                )
            ]

            branches_inventory = []
            branch_stocks = frappe.get_all(  # pylint: disable=no-member
                "branch doc",
                fields=["branch as branch_id"],
                filters={"parent": product.name, "parenttype": "Item"},
            )
            item_price = frappe.get_value(  # pylint: disable=no-member
                "Item Price", {"item_code": product.name}, "price_list_rate"
            )
            for stock in branch_stocks:
                branch_name = frappe.get_value(  # pylint: disable=no-member
                    "Branch",
                    {"name": stock.branch_id},
                    ["warehouse", "branch", "stock"],
                    as_dict=True,
                )

                branches_inventory.append(
                    {
                        "branch_id": stock.branch_id,
                        "branch_name": branch_name.branch,
                        "warehouse_name": branch_name.warehouse,  # Or fetch from somewhere if available
                        "stock": branch_name.stock,  # Or fetch from Bin doctype if available
                    }
                )

            product_list_data.append(
                {
                    "product_id": int(product.name),
                    "product_name": product.item_name,
                    "sku": int(product.sku),
                    "price": item_price,
                    "main_image": product.image,
                    "media": media_list,
                    "branches_inventory": branches_inventory,
                }
            )

        return Response(
            json.dumps(product_list_data), status=200, mimetype="application/json"
        )

    except Exception as e:
        return Response(
            json.dumps({"error": str(e)}),
            status=500,
            mimetype="application/json",
        )
