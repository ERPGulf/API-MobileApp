import frappe
import base64
from werkzeug.wrappers import Response, Request
import json
from frappe.utils import now_datetime


@frappe.whitelist()  # pylint: disable=no-member
def categories_List():
    """
    Returns a list of all categories.
    """
    # noinspection PyUnresolvedReferences
    doc = frappe.db.get_all(  # pylint: disable=no-member
        "Item Group", fields=["name as id ", "name"]
    )
    return Response(json.dumps({"data": doc}), status=200, mimetype="application/json")


@frappe.whitelist()  # pylint: disable=no-member
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
                "product_id": item["item_code"],  # assuming item_code is numeric
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
                    (customer["id"])
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


@frappe.whitelist()  # pylint: disable=no-member
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


@frappe.whitelist()  # pylint: disable=no-member
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


@frappe.whitelist()  # pylint: disable=no-member
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


@frappe.whitelist()  # pylint: disable=no-member
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


@frappe.whitelist()  # pylint: disable=no-member
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


@frappe.whitelist()  # pylint: disable=no-member
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


@frappe.whitelist()  # pylint: disable=no-member
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


@frappe.whitelist()  # pylint: disable=no-member
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


from frappe.auth import LoginManager  # pylint: disable=no-member
from frappe import _


@frappe.whitelist()
def custom_login(usr, pwd):
    try:
        login_manager = LoginManager()
        login_manager.authenticate(usr, pwd)
        login_manager.post_login()

        user = frappe.get_doc("User", usr)

        response = {
            "message": "Login successful",
            "sid": frappe.session.sid,
            "user_id": user.name,
            "full_name": user.full_name,
            "email": user.email,
        }
        return response

    except frappe.AuthenticationError as e:
        frappe.local.response.http_status_code = 401
        return {"message": str(e)}

    except Exception as e:
        frappe.local.response.http_status_code = 500
        return {"message": f"Error: {str(e)}"}


import requests


@frappe.whitelist(allow_guest=True)
def generate_token_secure(api_key, api_secret, app_key):
    # frappe.log_error(title='Login attempt',message=str(api_key) + str(api_secret) + str(app_key + "  "))
    try:
        try:
            app_key = base64.b64decode(app_key).decode("utf-8")
        except Exception as e:
            return Response(
                json.dumps(
                    {"message": "Security Parameters are not valid", "user_count": 0}
                ),
                status=401,
                mimetype="application/json",
            )
        clientID, clientSecret, clientUser = frappe.db.get_value(
            "OAuth Client",
            {"app_name": app_key},
            ["client_id", "client_secret", "user"],
        )

        if clientID is None:
            # return app_key
            return Response(
                json.dumps(
                    {"message": "Security Parameters are not valid", "user_count": 0}
                ),
                status=401,
                mimetype="application/json",
            )

        client_id = clientID  # Replace with your OAuth client ID
        client_secret = clientSecret  # Replace with your OAuth client secret
        url = (
            frappe.local.conf.host_name
            + "/api/method/frappe.integrations.oauth2.get_token"
        )
        payload = {
            "username": api_key,
            "password": api_secret,
            "grant_type": "password",
            "client_id": client_id,
            "client_secret": client_secret,
            # "grant_type": "refresh_token"
        }
        files = []
        headers = {"Content-Type": "application/json"}
        response = requests.request("POST", url, data=payload, files=files)
        if response.status_code == 200:
            result_data = json.loads(response.text)
            return Response(
                json.dumps({"data": result_data}),
                status=200,
                mimetype="application/json",
            )

        else:
            frappe.local.response.http_status_code = 401
            return json.loads(response.text)

    except Exception as e:
        # frappe.local.response.http_status_code = 401
        # return json.loads(response.text)
        return Response(
            json.dumps({"message": e, "user_count": 0}),
            status=500,
            mimetype="application/json",
        )


@frappe.whitelist(allow_guest=False)
def generate_token_secure_for_users(username, password, app_key):

    # return Response(json.dumps({"message": "2222 Security Parameters are not valid" , "user_count": 0}), status=401, mimetype='application/json')
    frappe.log_error(
        title="Login attempt",
        message=str(username) + "    " + str(password) + "    " + str(app_key + "  "),
    )
    try:
        try:
            app_key = base64.b64decode(app_key).decode("utf-8")
        except Exception as e:
            return Response(
                json.dumps(
                    {"message": "Security Parameters are not valid", "user_count": 0}
                ),
                status=401,
                mimetype="application/json",
            )
        clientID, clientSecret, clientUser = frappe.db.get_value(
            "OAuth Client",
            {"app_name": app_key},
            ["client_id", "client_secret", "user"],
        )

        if clientID is None:
            # return app_key
            return Response(
                json.dumps(
                    {"message": "Security Parameters are not valid", "user_count": 0}
                ),
                status=401,
                mimetype="application/json",
            )

        client_id = clientID  # Replace with your OAuth client ID
        client_secret = clientSecret  # Replace with your OAuth client secret
        url = (
            frappe.local.conf.host_name
            + "/api/method/frappe.integrations.oauth2.get_token"
        )
        payload = {
            "username": username,
            "password": password,
            "grant_type": "password",
            "client_id": client_id,
            "client_secret": client_secret,
            # "grant_type": "refresh_token"
        }
        files = []
        headers = {"Content-Type": "application/json"}
        response = requests.request("POST", url, data=payload, files=files)
        # var = frappe.get_list("Customer", fields=["name as id", "full_name","email", "mobile_no as phone",], filters={'name': ['like', username]})

        if response.status_code == 200:
            response_data = json.loads(response.text)

            result = {
                "token": response_data,
            }
            return Response(
                json.dumps({"data": result}), status=200, mimetype="application/json"
            )
        else:

            frappe.local.response.http_status_code = 401
            return json.loads(response.text)

    except Exception as e:
        # frappe.local.response.http_status_code = 401
        # return json.loads(response.text)
        return Response(
            json.dumps({"message": e, "user_count": 0}),
            status=500,
            mimetype="application/json",
        )


@frappe.whitelist(allow_guest=True)
def create_refresh_token(refresh_token):
    url = (
        frappe.local.conf.host_name + "/api/method/frappe.integrations.oauth2.get_token"
    )
    payload = f"grant_type=refresh_token&refresh_token={refresh_token}"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    files = []

    response = requests.post(url, headers=headers, data=payload, files=files)

    if response.status_code == 200:
        try:

            message_json = json.loads(response.text)

            new_message = {
                "access_token": message_json["access_token"],
                "expires_in": message_json["expires_in"],
                "token_type": message_json["token_type"],
                "scope": message_json["scope"],
                "refresh_token": message_json["refresh_token"],
            }

            return Response(
                json.dumps({"data": new_message}),
                status=200,
                mimetype="application/json",
            )
        except json.JSONDecodeError as e:
            return Response(
                json.dumps({"data": f"Error decoding JSON: {e}"}),
                status=401,
                mimetype="application/json",
            )
    else:

        return Response(
            json.dumps({"data": response.text}), status=401, mimetype="application/json"
        )
