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


import json


@frappe.whitelist(allow_guest=True)
def create_customer():

    try:
        data = json.loads(frappe.request.data)
    except Exception as e:
        return Response(
            json.dumps({"error": f"Invalid JSON input: {str(e)}"}),
            status=400,
            mimetype="application/json",
        )

    required_fields = ["name", "phone", "email", "country_code"]
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return Response(
            json.dumps(
                {"error": f"Missing required fields: {', '.join(missing_fields)}"}
            ),
            status=400,
            mimetype="application/json",
        )

    existing_customer = frappe.get_all(
        "Customer",
        filters={
            "name": data.get("customer_id"),
        },
        fields=["name"],
        limit=1,
    )

    business_details = frappe.get_doc(
        {
            "doctype": "businessDetails",
            "title": data.get("name"),
            "vatnumber": data.get("vat_number"),
            "addressprooffront": data.get("address_proof_front"),
            "addressproofback": data.get("address_proof_back"),
            "crdocumentfront": data.get("cr_document_front"),
            "crdocumentback": data.get("cr_document_back"),
            "crnumber": data.get("cr_number"),
            "vatdocfront": data.get("vat_doc_front"),
            "vatdocback": data.get("vat_doc_back"),
            "idprooffront": data.get("id_proof_front"),
            "idproofback": data.get("id_proof_back"),
            "shopimagefront": data.get("shop_image_front"),
            "shopimageback": data.get("shop_image_back"),
        }
    )
    business_details.insert(ignore_permissions=True)

    customer_data = {
        "customer_name": data.get("name"),
        "mobile_no": data.get("phone"),
        "email_id": data.get("email"),
        "custom_country_code": data.get("country_code"),
        "custom_addedtype": data.get("added_type"),
        "custom_user_id_copy": data.get("user_id"),
        "custom_channelid": data.get("channel_id"),
        "custom_classification": data.get("classification"),
        "custom_profile_image": data.get("profile_image"),
        "custom_first_name": data.get("first_name"),
        "custom_last_name": data.get("last_name"),
        "customer_primary_address": data.get("address"),
        "custom_business_name": business_details.name,
    }

    if existing_customer:
        customer = frappe.get_doc("Customer", existing_customer[0].name)
        customer.update(customer_data)
        customer.save(ignore_permissions=True)
        message = "Customer updated successfully"
    else:
        user = frappe.get_doc(
            {
                "doctype": "User",
                "first_name": data.get("first_name") or data.get("name"),
                "last_name": data.get("last_name"),
                "email": data.get("email"),
                "mobile_no": data.get("phone"),
                "send_welcome_email": 0,
                "user_type": "Website User",
            }
        )
        user.insert(ignore_permissions=True)
        customer = frappe.get_doc({"doctype": "Customer", **customer_data})
        customer.insert(ignore_permissions=True)
        message = "Customer created successfully"

    response_data = {
        "customer_name": customer.customer_name,
        "customer_id": customer.name,
        "mobile_no": customer.mobile_no,
        "email_id": customer.email_id,
        "country_code": customer.custom_country_code,
        "profile_image": customer.custom_profile_image,
        "classification": customer.custom_classification,
        "added_type": customer.custom_addedtype,
        "user_id": customer.custom_user_id_copy,
        "channel_id": customer.custom_channelid,
        "first_name": customer.custom_first_name,
        "last_name": customer.custom_last_name,
        "address": customer.customer_primary_address,
        "business_details": {
            "business_id": business_details.name,
            "title": business_details.title,
            "vat_number": business_details.vatnumber,
            "cr_number": business_details.crnumber,
            "documents": {
                "address_proof_front": business_details.addressprooffront,
                "address_proof_back": business_details.addressproofback,
                "cr_document_front": business_details.crdocumentfront,
                "cr_document_back": business_details.crdocumentback,
                "vat_doc_front": business_details.vatdocfront,
                "vat_doc_back": business_details.vatdocback,
                "id_proof_front": business_details.idprooffront,
                "id_proof_back": business_details.idproofback,
                "shop_image_front": business_details.shopimagefront,
                "shop_image_back": business_details.shopimageback,
            },
        },
    }

    return Response(
        json.dumps({"message": message, "data": response_data}),
        status=200,
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

    customer_name = customer[0]["name"]

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


@frappe.whitelist(allow_guest=True)
def create_item():
    import json
    from frappe import _

    try:
        data = json.loads(frappe.request.data)
    except Exception as e:
        return Response(
            json.dumps({"error": f"Invalid JSON input: {str(e)}"}),
            status=400,
            mimetype="application/json",
        )

    item_code = data.get("skuCode")
    if not item_code:
        return Response(
            json.dumps({"error": "skuCode (item_code) is required."}),
            status=400,
            mimetype="application/json",
        )

    existing_item = frappe.db.exists("Item", {"item_code": item_code})

    if existing_item:

        item = frappe.get_doc("Item", existing_item)

        field_mapping = {
            "nameEn": "item_name",
            "brand": "custom_brand_id",
            "descriptionEn": "description",
            "nameAr": "custom_name_arabic",
            "nameHi": "custom_namehi",
            "nameUr": "custom_nameur",
            "descriptionAr": "custom_descriptionar",
            "descriptionHi": "custom_descriptionhi",
            "descriptionUr": "custom_descriptionur",
        }

        for json_key, docfield in field_mapping.items():
            if json_key in data:
                item.set(docfield, data.get(json_key))

        if "channelCatSubCat" in data:
            item.set("custom_channelcatsubcat", [])
            for row in data.get("channelCatSubCat", []):
                item.append(
                    "custom_channelcatsubcat",
                    {
                        "doctype": "channelCatSubCat",
                        "channelid": row.get("channelid"),
                        "categoryid": row.get("categoryid"),
                        "subcategoryid": row.get("subCategoryid"),
                    },
                )

        if "subCatImg" in data:
            item.set("media", [])
            for url in data.get("subCatImg", []):
                item.append("media", {"doctype": "media", "media": url})

        item.save(ignore_permissions=True)
        message = "Item updated successfully"

    else:

        channel_cat_sub_cat_children = (
            [
                {
                    "doctype": "channelCatSubCat",
                    "channelid": row.get("channelid"),
                    "categoryid": row.get("categoryid"),
                    "subcategoryid": row.get("subCategoryid"),
                }
                for row in data.get("channelCatSubCat", [])
            ]
            if "channelCatSubCat" in data
            else []
        )

        media_children = (
            [
                {
                    "doctype": "media",
                    "media": url,
                }
                for url in data.get("subCatImg", [])
            ]
            if "subCatImg" in data
            else []
        )

        item = frappe.get_doc(
            {
                "doctype": "Item",
                "item_code": item_code,
                "item_group": "Products",
            }
        )

        field_mapping = {
            "nameEn": "item_name",
            "brand": "custom_brand_id",
            "descriptionEn": "description",
            "nameAr": "custom_name_arabic",
            "nameHi": "custom_namehi",
            "nameUr": "custom_nameur",
            "descriptionAr": "custom_descriptionar",
            "descriptionHi": "custom_descriptionhi",
            "descriptionUr": "custom_descriptionur",
        }

        for json_key, docfield in field_mapping.items():
            if json_key in data:
                item.set(docfield, data.get(json_key))

        for row in channel_cat_sub_cat_children:
            item.append("custom_channelcatsubcat", row)

        for media in media_children:
            item.append("media", media)

        item.insert(ignore_permissions=True)
        message = "Item created successfully"

    channel_catsubcats = [
        {
            "channelid": row.channelid,
            "categoryid": row.categoryid,
            "subcategoryid": row.subcategoryid,
        }
        for row in item.custom_channelcatsubcat
    ]

    media_urls = [m.media for m in item.media]

    response_data = {
        "name": item.name,
        "item_code": item.item_code,
        "item_name": item.item_name,
        "description": item.description,
        "brand": item.custom_brand_id,
        "channelCatSubCat": channel_catsubcats,
        "media": media_urls,
    }

    return Response(
        json.dumps({"message": message, "data": response_data}),
        status=200,
        mimetype="application/json",
    )


@frappe.whitelist(allow_guest=True)
def create_or_update_warehouse():
    try:
        data = json.loads(frappe.request.data)
    except Exception as e:
        return Response(
            json.dumps({"error": f"Invalid JSON input: {str(e)}"}),
            status=400,
            mimetype="application/json",
        )

    warehouse_name = data.get("warehouse_name")
    if not warehouse_name:
        return Response(
            json.dumps({"error": "warehouse_name is required."}),
            status=400,
            mimetype="application/json",
        )

    existing_warehouse = frappe.db.exists(
        "Warehouse", {"warehouse_name": warehouse_name}
    )

    if existing_warehouse:

        warehouse = frappe.get_doc("Warehouse", existing_warehouse)

        if "address_line_1" in data:
            warehouse.address_line_1 = data.get("address_line_1")
        if "region" in data:
            warehouse.custom_region = data.get("region")
        if "warehouse_code" in data:
            warehouse.custom_warehouse_code = data.get("warehouse_code")

        warehouse.save(ignore_permissions=True)
        message = "Warehouse updated successfully"

    else:

        warehouse = frappe.get_doc(
            {
                "doctype": "Warehouse",
                "warehouse_name": warehouse_name,
                "address_line_1": data.get("address_line_1", ""),
                "custom_region": data.get("region", ""),
                "custom_warehouse_code": data.get("warehouse_code", ""),
            }
        )

        warehouse.insert(ignore_permissions=True)
        message = "Warehouse created successfully"

    warehouse_data = {
        "name": warehouse.name,
        "warehouse_name": warehouse.warehouse_name,
        "address_line_1": warehouse.address_line_1,
        "region": warehouse.custom_region,
        "warehouse_code": warehouse.custom_warehouse_code,
    }

    return Response(
        json.dumps({"message": message, "data": warehouse_data}),
        status=200,
        mimetype="application/json",
    )


@frappe.whitelist(allow_guest=True)
def create_or_update_order():
    import json
    from frappe import _

    try:
        data = json.loads(frappe.request.data)
    except Exception as e:
        return Response(
            json.dumps({"error": f"Invalid JSON input: {str(e)}"}),
            status=400,
            mimetype="application/json",
        )

    if not data.get("user_id"):
        return Response(
            json.dumps({"error": "user_id is required."}),
            status=400,
            mimetype="application/json",
        )

    if not data.get("items"):
        return Response(
            json.dumps({"error": "items list is required."}),
            status=400,
            mimetype="application/json",
        )

    invoice_items = []
    for item in data.get("items", []):
        if not frappe.db.exists("Item", {"name": item["item_code"]}):
            continue

        invoice_items.append(
            {
                "item_code": item["item_code"],
                "qty": item.get("quantity", 0),
                "rate": item.get("price", 0),
                "delivery_date": item.get("delivery_date", frappe.utils.nowdate()),
                "uom": item.get("uom", "Nos"),
                "warehouse": item.get("warehouse", "All Warehouses - erp"),
            }
        )

    if not invoice_items:
        return Response(
            json.dumps({"error": "No valid items found for order."}),
            status=400,
            mimetype="application/json",
        )

    sales_team = []
    if data.get("sales_man_name"):
        sales_team.append(
            {"sales_person": data.get("sales_man_name"), "allocated_percentage": 100}
        )
    existing_order = None
    if data.get("order_id"):
        existing_order = frappe.db.exists("Sales Order", {"name": data.get("order_id")})

    if existing_order:

        order = frappe.get_doc("Sales Order", existing_order)

        order.discount_amount = data.get("discount_amount", order.discount_amount)
        order.grand_total = data.get("total", order.grand_total)
        order.coupon_code = data.get("promotion_code", order.coupon_code)
        order.branch_id = data.get("branch_id", order.branch_id)
        order.custom_orderby = data.get("orderby", order.custom_orderby)
        order.address_display = data.get("address_display", order.address_display)
        order.shipping_address = data.get("shipping_address", order.shipping_address)
        order.custom_region = data.get("region", order.custom_region)
        order.custom_payment_options = data.get(
            "payment_options", order.custom_payment_options
        )

        order.set("items", [])
        for item in invoice_items:
            order.append("items", item)

        order.set("sales_team", [])
        for sales_person in sales_team:
            order.append("sales_team", sales_person)

        order.save(ignore_permissions=True)
        message = "Sales Order updated successfully"

    else:

        order = frappe.get_doc(
            {
                "doctype": "Sales Order",
                "customer": data.get("user_id"),
                "items": invoice_items,
                "discount_amount": data.get("discount_amount", 0),
                "grand_total": data.get("total", 0),
                "coupon_code": data.get("promotion_code"),
                "custom_orderby": data.get("orderby", 1),
                "custom_region": data.get("region", ""),
                "address_display": data.get("address_display", ""),
                "shipping_address": data.get("shipping_address", ""),
                "sales_team": sales_team,
                "custom_payment_options": data.get("payment_options", "COD"),
            }
        )

        order.insert(ignore_permissions=True)
        message = "Sales Order created successfully"

    items_data = [
        {
            "item_code": i.item_code,
            "qty": i.qty,
            "rate": i.rate,
            "uom": i.uom,
            "warehouse": i.warehouse,
        }
        for i in order.items
    ]

    sales_team_data = [
        {
            "sales_person": st.sales_person,
            "allocated_percentage": st.allocated_percentage,
        }
        for st in order.sales_team
    ]

    order_data = {
        "name": order.name,
        "customer": order.customer,
        "grand_total": order.grand_total,
        "total_qty": order.total_qty,
        "discount_amount": order.discount_amount,
        "status": order.status,
        "items": items_data,
        "sales_team": sales_team_data,
        "coupon_code": order.coupon_code,
        "orderby": order.custom_orderby,
        "billing address": order.address_display,
        "shipping_address": order.shipping_address,
        "region": order.custom_region,
        "payment_options": order.custom_payment_options,
    }

    return Response(
        json.dumps({"message": message, "data": order_data}),
        status=200,
        mimetype="application/json",
    )
