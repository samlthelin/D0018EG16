from flask import Flask, render_template, g, request, redirect, url_for, session
import json
import mysql.connector
import random

app = Flask(__name__)
app.secret_key = 'hej'

db_config = {
    "host": "d0018egroup16.cncg2uywo7t4.eu-north-1.rds.amazonaws.com",
    "user": "admin",
    "password": "Group161337!",
    "database": "timsfränadatabas",
}

# Homepage
@app.route("/")
def index():
    if 'logged_in' not in session:
        session['logged_in'] = False
        session['username'] = ""
        session['userid'] = ""
    # Querya databasen på alla produkter i products
    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()
    cursor.execute("SELECT * FROM products;")
    # SELECT products.*, reviews.userid, reviews.review FROM timsfränadatabas.products JOIN timsfränadatabas.reviews ON products.productid=reviews.productid;
    data = cursor.fetchall()
    db.commit()
    cursor.close()
    db.close()
    # Skickar vidare det i en html template
    return render_template("index.html", data=data, logged_in=session['logged_in'])

@app.route("/search_order", methods=["POST"])
def notLoggedInOrderSearch():
    searchOrderID = json.loads(request.cookies.get('orderSearchInput'))
    print("-------> Det ID du sökte efter var: ",searchOrderID)
    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()

    orderID_query="""SELECT orders.orderid, orders.customeremail, orders.customeradress, orders.customernumber,orders.kvittoorderid, receipts.productname, receipts.productcost FROM timsfränadatabas.orders JOIN receipts ON orders.kvittoorderid=receipts.kvittoorderid WHERE orders.orderid=%s;"""
    cursor.execute(orderID_query, (searchOrderID,))
    result = cursor.fetchall()
    db.commit()
    cursor.close()
    db.close()
    
    return render_template("index2.html", result=result)


@app.route("/login_authentication", methods=["POST"])
def login_to_account():
    loginVariablesArray = json.loads(request.cookies.get("loginVariablesArray"))
    username = loginVariablesArray[0]
    password = loginVariablesArray[1]
    print("the username given and password given: ", username, password)

    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()

    search_query = "SELECT * FROM users WHERE `username`=%s AND `password`=%s;"
    cursor.execute(search_query, (username, password))

    result = cursor.fetchone()
    db.commit()
    cursor.close()
    db.close()
    
    if result:
        print(f"Username and password combo found")

        db = mysql.connector.connect(**db_config)
        cursor = db.cursor()
        
        search_query = "SELECT userid FROM users WHERE `username`=%s AND `password`=%s;"
        cursor.execute(search_query, (username, password))
   
        userid = cursor.fetchone()
        useridToNotTuple = userid[0]
        db.commit()
        cursor.close()
        db.close()
        print(useridToNotTuple)
        session['userid'] = useridToNotTuple
        session['username'] = username
        session['logged_in'] = True
        

        return redirect(url_for("index"))
    
    else:
        print(f"User and pass combo not found in table")
        return redirect(url_for("index"))
    


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route("/submit_user", methods=["POST"])
def create_account():
    userVariablesArray = json.loads(request.cookies.get("userVariablesArray"))
    userid = random.randint(1000, 9999)
    username = userVariablesArray[0]
    password = userVariablesArray[1]
    email = userVariablesArray[2]
    #print(username, password, email)
    # Handle the user data as needed

    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()

    insert_query = """INSERT INTO `users` (userid, username, password, email)
    VALUES (%s, %s, %s, %s)"""
    cursor.execute(insert_query,(userid,username,password,email),)
    
    db.commit()
    cursor.close()
    db.close()

    return redirect(url_for("index"))

@app.route("/purchasehistory")
def purchasehistory():
    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()
    userid = session['userid']
    search_query="""SELECT orders.orderid, orders.customeremail, orders.customeradress, orders.customernumber,orders.kvittoorderid, receipts.productname, receipts.productcost FROM timsfränadatabas.orders JOIN receipts ON orders.kvittoorderid=receipts.kvittoorderid WHERE orders.userid=%s;"""
    data = cursor.execute(search_query, (userid,))
    result = cursor.fetchall()
    return render_template("purchaseinformation.html", result=result)


# Beställnings formulär
@app.route("/order/")
def order():
    cartArray = json.loads(request.cookies.get("cartArray"))
    return render_template("order_form.html", cartArray=cartArray)





@app.route("/submit_order", methods=["POST"])
def submit_order():
    if session['logged_in']:
        userid = session['userid']
    else:
        userid = 0
    
    cartArray = json.loads(request.cookies.get("cartArray"))
    print("The cart contains:", cartArray)

    # Kod för att skicka input till databasen
    try:
        kvittoorderid = random.randint(1000, 9999)

        for cartArrayIndex in cartArray:
            productid = int(cartArrayIndex[0])
            productname = cartArrayIndex[1]
            productcost = int(cartArrayIndex[2])
            productimagefilepath = cartArrayIndex[3]
            productcountryoforigin = cartArrayIndex[4]
            kvittoid = random.randint(1000, 9999)

            print(
                productid,
                productname,
                productcost,
                productimagefilepath,
                productcountryoforigin
            )
            db = mysql.connector.connect(**db_config)
            cursor = db.cursor()

            insert_query = """
                INSERT INTO `receipts` (kvittoid, kvittoorderid, productid, productname, productcost, productimagefilepath, productcountryoforigin)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
            cursor.execute(
                insert_query,
                (
                    kvittoid,
                    kvittoorderid,
                    productid,
                    productname,
                    productcost,
                    productimagefilepath,
                    productcountryoforigin,
                ),
            )
            print("Passed receipts")
            db.commit()
            cursor.close()
            db.close()

        # Konverterar input från formulär till python variabler
        # productid = request.form.get('productid')
        customeremail = request.form.get("customeremail")
        customeradress = request.form.get("customeradress")
        customernumber = request.form.get("customerphone")

        # Connection till databasen
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor()

        # Anger ett random orderid, samt säkerställer att productid behandlas som en int
        orderid = random.randint(1000, 9999)

        # productid = int(productid)

        # Skapa ett MySQL commando för att insert input
        insert_query = """
            INSERT INTO orders (orderid, kvittoorderid, customeremail, customeradress, customernumber, userid)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            insert_query,
            (orderid, kvittoorderid, customeremail, customeradress, customernumber, userid),
        )

        # Commitar databas ändringarna och stänger db connection för att undvika felaktiga cursors
        db.commit()
        cursor.close()
        db.close()

        db = mysql.connector.connect(**db_config)
        cursor = db.cursor()

        # Går tillbaka till index
        return redirect(url_for("index"))

    except Exception as e:
        # Fångar problem vid uppladdning till databas
        print(f"Error submitting order: {e}")
        return render_template("error.html", error_message="Error submitting order")


if __name__ == "__main__":
    app.run(debug=True)