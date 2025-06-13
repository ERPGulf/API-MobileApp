## Jawad

Jawad custom ERP app



## 🔧 Installation Guide
Follow these steps to install **Jawad app** :


### 1️⃣ Prerequisites
- You must have **ERPNext** installed and running.
- Install **Python** (>=3.8) and **Frappe Framework**.


### 2️⃣ Clone the Repository
Open your terminal and run:
```bash
git clone https://github.com/ERPGulf/API-MobileApp.git
cd API-MobileApp
```

### 3️⃣ Install Dependencies
Run the following command inside the project directory:
```bash
pip install -r requirements.txt
```

### 4️⃣ Setup ERPNext App
Inside your ERPNext environment, install the app:
```bash
bench get-app jawad
bench --site your-site-name install-app jawad
```

### 5️⃣ Migrate and Restart
```bash
bench --site your-site-name migrate
bench restart
```

## 📖 API Documentation
### 🔸 Base URL:
`https://your-domain.com/api/method/jawad.jawad.apis.`

---

### 📚 Available APIs:

####  **categories_List API**
- **Method:** `GET`
- **URL:** `api/method/jawad.jawad.apis.`
- **Description:** This api retrieve all available product categorie.
- **Response**
```bash
{
    "data": [
        {
            "id": 1,
            "name": "Electronics"
        },
        {
            "id": 2,
            "name": "Groceries"
        }
    ]
}
```

#### **updated_or_newly_added_items**
- **Method:** `GET`
- **URL:** `api/method/jawad.jawad.apis.updated_or_newly_added_items`
- **Description:** TThis api retrieve products, customers that were recently updated or newly
added.

- **Response**
```bash
{
    "products": [
        {
            "product_id": 105,
            "product_name": "iPhone 15",
            "updated_at": "2025-06-05 09:21:51.599398"
        }
    ],
    "customers": [
        {
            "id": "C-00091",
            "name": "testing50",
            "updated_at": "2025-06-03 11:55:54.737872"
        },
        {
            "id": "C-00092",
            "name": "test51",
            "updated_at": "2025-06-03 13:04:34.349446"
        },
        {
            "id": "C-00027",
            "name": "testing 40",
            "updated_at": "2025-06-04 07:23:10.706087"
        },
        {
            "id": "Aysha",
            "name": "abc",
            "updated_at": "2025-06-12 07:23:16.532035"
        },
        {
            "id": "C-00093",
            "name": "testing 49",
            "updated_at": "2025-06-12 08:32:47.842237"
        },
        {
            "id": "C-00094",
            "name": "testing 50",
            "updated_at": "2025-06-12 09:27:58.881550"
        }
    ]
}
```

####  **valid_promotion_list**
- **Method:** `GET`
- **URL:** `api/method/jawad.jawad.apis.valid_promotion_list`
- **Description:** This api retrieve currently active promotional offers.
- **Response**
```bash
{
    "data": [
        {
            "name": "KSA10",
            "percentage": "Discount Percentage",
            "value": 10.0,
            "valid_from": "2025-06-03",
            "valid_upto": "2025-06-20"
        }
    ]
}
```
####  **customer list**
- **Method:** `GET`
- **URL:** `api/method/jawad.jawad.apis.customer_list`
- **Description:** This api will fetch all customers in the system.
- **Response**
```bash
{
    "data": [
        {
            "id": "sithara",
            "name": "sithara",
            "phone": "919961343245",
            "email": ""
        },
        {
            "id": "testing sales",
            "name": "testing sales",
            "phone": "097455124924",
            "email": ""
        },
        {
            "id": "new_one",
            "name": "new_one",
            "phone": "1237655544",
            "email": ""
        },
        {
            "id": "aysha - 1",
            "name": "aysha",
            "phone": null,
            "email": null
        },]}
```
#### **create customer**
- **Method:** `POST`
- **URL:** `api/method/jawad.jawad.apis.create_customer`
- **Description:** This api used to create customer.
- **Response**
```bash
{
    "message": "Customer created successfully",
    "id": "C-00095"
}
```
#### **update_customer**
- **Method:** `Put`
- **URL:** `api/method/jawad.jawad.apis.update_customer`
- **Description:** Api used to update customer , here we need to pass name and the phone number which we need to update.
- **Response**
```bash
{
    "message": "Customer phone number updated successfully"
}
```

#### **post_order**
- **Method:** `POST`
- **URL:** `api/method/jawad.jawad.apis.post_order`
- **Description:** Api to post order , here we pass the required arguments to create an order.
- **Response**
```bash
{
    "message": "Order created successfully",
    "id": "SAL-ORD-2025-00005"
}
```
#### **order_list**
- **Method:** `GET`
- **URL:** `api/method/jawad.jawad.apis.order_list`
- **Description:** Api used to list orders , response should be like orderid, date and total.
- **Response**
```bash
{
    "data": [
        {
            "id": "SAL-ORD-2025-00005",
            "date": "2025-06-13",
            "total": 500.0
        },
        {
            "id": "SAL-ORD-2025-00004",
            "date": "2025-06-04",
            "total": 500.0
        },
        {
            "id": "SAL-ORD-2025-00002",
            "date": "2025-06-04",
            "total": 0.0
        },
        {
            "id": "SAL-ORD-2025-00001",
            "date": "2025-06-04",
            "total": 2.0
        }
    ]
}
```
#### **branches_list**
- **Method:** `GET`
- **URL:** `api/method/jawad.jawad.apis.branches_list`
- **Description:** Api used to list branches and response contain id, city and name
- **Response**
```bash
{
    "data": [
        {
            "id": 1,
            "name": "Riyadh - Tahlia Branch",
            "city": "Riyadh"
        },
        {
            "id": 2,
            "name": "Jeddah - Andalus Branch",
            "city": "jeddah"
        }
    ]
}
```
#### **product_list**
- **Method:** `GET`
- **URL:** `api/method/jawad.jawad.apis.product_list`
- **Description:** Api used to list the products when we pass the product id and get response of the specific product details like id, branches,item, image etc.
- **Response**
```bash
[
    {
        "product_id": 105,
        "product_name": "iPhone 15",
        "sku": 1213,
        "price": 4599.0,
        "main_image": "/files/123.png",
        "media": [
            "/files/123.png",
            "/files/scr.png"
        ],
        "branches_inventory": [
            {
                "branch_id": "1",
                "branch_name": "Riyadh - Tahlia Branch",
                "warehouse_name": "All Warehouses - erp",
                "stock": 3
            },
            {
                "branch_id": "2",
                "branch_name": "Jeddah - Andalus Branch",
                "warehouse_name": null,
                "stock": 0
            }
        ]
    }
]
```
# 👤 Author
Aysha Sithara.