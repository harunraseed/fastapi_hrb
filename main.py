from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pyodbc

app = FastAPI()

# Enable CORS for the FastAPI backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SQL Server connection details
connection_string = (
    "Driver={SQL Server};"
    "Server=localhost;"  # Replace with your server name
    "Database=hrb_db;"  # Replace with your database name
    "Trusted_Connection=yes;"
)

class CustomerOrder(BaseModel):
    customer_name: str
    customer_email: str
    order_date: str  # Ensure the format is consistent (e.g., 'YYYY-MM-DD')
    order_amount: float

@app.post("/add_customer_order/")
async def add_customer_order(order: CustomerOrder):
    try:
        with pyodbc.connect(connection_string) as conn:
            cursor = conn.cursor()
            customer_id = cursor.execute("""
                DECLARE @CustomerID INT;
                EXEC AddCustomerAndOrder @CustomerName=?, @CustomerEmail=?, @OrderDate=?, @OrderAmount=?, @CustomerID=@CustomerID OUTPUT;
                SELECT @CustomerID;
            """, order.customer_name, order.customer_email, order.order_date, order.order_amount).fetchval()

            # Check if a valid customer_id was returned
            if customer_id is None:
                raise HTTPException(status_code=500, detail="Failed to add customer and order")

        return {"message": "Customer and Order added successfully", "customer_id": customer_id}

    except pyodbc.Error as db_err:
        raise HTTPException(status_code=500, detail=f"Database error occurred: {str(db_err)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.get("/customer_orders/{customer_id}")
async def get_customer_orders(customer_id: int):
    try:
        with pyodbc.connect(connection_string) as conn:
            cursor = conn.cursor()
            
            # Check if the customer exists
            customer_exists = cursor.execute("""
                SELECT COUNT(*) FROM Customers WHERE CustomerID=?
            """, customer_id).fetchval()

            if customer_exists == 0:
                return {"message": f"No customer available for Customer ID {customer_id}"}
            
            # Retrieve orders for the customer
            orders = cursor.execute(""" 
                EXEC GetCustomerOrders @CustomerID=? 
            """, customer_id).fetchall()

            if not orders:
                return {"message": "No orders found for this customer"}

            result = [
                {
                    "CustomerID": order[0],
                    "CustomerName": order[1],
                    "CustomerEmail": order[2],
                    "OrderID": order[3],
                    "OrderDate": order[4],
                    "OrderAmount": order[5]
                } for order in orders
            ]

        return result

    except pyodbc.Error as db_err:
        raise HTTPException(status_code=500, detail=f"Database error occurred: {str(db_err)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


@app.delete("/delete_customer/{customer_id}")
async def delete_customer(customer_id: int):
    try:
        with pyodbc.connect(connection_string) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                EXEC DeleteCustomer @CustomerID=?
            """, customer_id)

            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Customer not found")

        return {"message": f"Customer with ID {customer_id} deleted successfully"}

    except pyodbc.Error as db_err:
        raise HTTPException(status_code=500, detail=f"Database error occurred: {str(db_err)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.delete("/delete_order/{order_id}")
async def delete_order(order_id: int):
    try:
        with pyodbc.connect(connection_string) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                EXEC DeleteOrder @OrderID=?
            """, order_id)

            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Order not found")

        return {"message": "Order deleted successfully"}

    except pyodbc.Error as db_err:
        raise HTTPException(status_code=500, detail=f"Database error occurred: {str(db_err)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.get("/get_orders/{customer_id}")
async def get_orders(customer_id: int):
    try:
        with pyodbc.connect(connection_string) as conn:
            cursor = conn.cursor()
            
            # Check if the customer exists first
            customer_exists = cursor.execute("""
                SELECT COUNT(*) FROM Customers WHERE CustomerID=?
            """, customer_id).fetchval()

            if customer_exists == 0:
                return {"message": f"No customer found for ID {customer_id}"}
            
            orders = cursor.execute("""
                EXEC GetCustomerOrders @CustomerID=?
            """, customer_id).fetchall()

            if not orders:
                return {"message": f"No orders found for customer ID {customer_id}"}

            result = [
                {
                    "OrderID": order[3],
                    "OrderDate": order[4],
                    "OrderAmount": order[5],
                    "CustomerName": order[1],
                    "CustomerEmail": order[2]
                } for order in orders
            ]

        return {"orders": result}

    except pyodbc.Error as db_err:
        raise HTTPException(status_code=500, detail=f"Database error occurred: {str(db_err)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
