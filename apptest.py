from flask import Flask, render_template, g, request, redirect, url_for, session
import json
import mysql.connector
import random
from datetime import date

app = Flask(__name__)
app.secret_key = 'hej'

db_config = {
    "host": "d0018egroup16.cncg2uywo7t4.eu-north-1.rds.amazonaws.com",
    "user": "admin",
    "password": "Group161337!",
    "database": "timsfränadatabas",
}

# SELECT reviews.userid, reviews.review FROM timsfränadatabas.reviews WHERE productid=1;
# 

# SELECT AVG(rating) AS averagerating FROM ratings WHERE productid=1;

# Homepage
@app.route("/")
def index():
    if 'logged_in' not in session:
        session['logged_in'] = False
        session['username'] = ""
        session['userid'] = 0
    # Querya databasen på alla produkter i products
    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()
    cursor.execute("SELECT * FROM products;")
    # SELECT products.*, reviews.userid, reviews.review FROM timsfränadatabas.products JOIN timsfränadatabas.reviews ON products.productid=reviews.productid;
    data = cursor.fetchall()
    temp = data[0]
    print("samuels print", )
    db.commit()
    cursor.close()
    db.close()
    # Skickar vidare det i en html template
    return render_template("index.html", data=data, logged_in=session['logged_in'], userid=session['userid'])


@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    
    productid=request.form['productid']

    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()

    if session['logged_in']:
        userid = session['userid']
        cartref = userid
    else:
        userid = 0
        cartref = random.randint(1000, 9999)

    reserveQuery = "SELECT stock, reservedAmount FROM timsfränadatabas.products WHERE productid=%s;"
    cursor.execute(reserveQuery, (productid,))
    res = cursor.fetchall()
    print(res)
    if(res[0][1] < res[0][0]):
        insertCartQuery="INSERT INTO cart (productid, customerid) VALUES (%s,%s)"
        cursor.execute(insertCartQuery, (productid,userid),)
        print("inserted item in cart, now updating reserved amount")
        updateQuery="UPDATE timsfränadatabas.products SET reservedAmount=reservedAmount+1 WHERE productid=%s"
        cursor.execute(updateQuery, (productid,))
        print("Reserved amount incremented by 1")
    else:
        print("item not added to cart, since the reserved amount is the exact amount of the stock")
    
    db.commit()
    cursor.close()
    db.close()

    return redirect(url_for("index"))

#Gör det möjligt att söka efter ordrar även om du inte är inloggad.
@app.route("/search_order", methods=["POST"])
def notLoggedInOrderSearch():
    searchOrderID = json.loads(request.cookies.get('orderSearchInput'))
    print("-------> Det ID du sökte efter var: ",searchOrderID)
    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()

    orderID_query="""SELECT orders.orderid, orders.customeremail, orders.customeradress, orders.customernumber,orders.kvittoorderid, orders.orderdate, receipts.productname, receipts.productcost FROM timsfränadatabas.orders JOIN receipts ON orders.kvittoorderid=receipts.kvittoorderid WHERE orders.orderid=%s;"""
    cursor.execute(orderID_query, (searchOrderID,))
    result = cursor.fetchall()
    db.commit()
    cursor.close()
    db.close()
    
    return render_template("purchaseinformation.html", result=result)


#Skickar en vidare till sidan där man kan se kommentarer och admin svar angående prdukten som du valt.
@app.route("/productInformation")
def productInformation():
    if 'logged_in' not in session:
        session['logged_in'] = False
        session['username'] = ""
        session['userid'] = 0
    selectedProduct = json.loads(request.cookies.get("selectedProduct"))
    print("you selected product:", selectedProduct)
    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()
    search_query = ("SELECT * FROM products WHERE productid=%s;")
    cursor.execute(search_query, (selectedProduct,))
    data = cursor.fetchone()
    db.commit()
    cursor.close()
    cursor = db.cursor()
    review_query = ("SELECT reviews.reviewid, reviews.review, users.username, reviews.response FROM reviews JOIN users ON reviews.userid=users.userid WHERE productid=%s;")
    cursor.execute(review_query, (selectedProduct,))
    review = cursor.fetchall()
    db.commit()
    cursor.close()

    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()

    avg_rating_query = "SELECT AVG(rating) AS averagerating FROM ratings WHERE productid=%s;"
    cursor.execute(avg_rating_query, (selectedProduct,))
    avgrating = cursor.fetchone()
    avgrating=avgrating[0]
    db.commit()
    cursor.close()

    #SELECT COUNT(*) FROM ratings WHERE userid = 'your_user_id';

    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()

    rating_query = "SELECT COUNT(*) FROM ratings WHERE userid = %s;"
    userid = session['userid']
    cursor.execute(rating_query,(userid,))
    ratingToF = cursor.fetchone()
    db.commit()
    cursor.close()
    db.close()

    print("data ------------ > ",data, type(data))

    return render_template("productinformation.html", ratingToF = ratingToF,data=data, review=review, selectedProduct=selectedProduct, logged_in=session['logged_in'], userid=session['userid'], avgrating=avgrating)

#Check för att se om man är inloggad.
@app.route("/login_authentication", methods=["POST"])
def login_to_account():
    loginVariablesArray = json.loads(request.cookies.get("loginVariablesArray"))
    username = loginVariablesArray[0]
    password = loginVariablesArray[1]
    currentPage = loginVariablesArray[2]
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
        print("------------> user id  :  ",userid)
        useridToNotTuple = userid[0]
        print("------------> to not tuple:  ",useridToNotTuple, "och den har typen : ",type(useridToNotTuple))
        db.commit()
        cursor.close()
        db.close()
        print(useridToNotTuple)
        session['userid'] = useridToNotTuple
        session['username'] = username
        session['logged_in'] = True
        print(currentPage)
        return redirect(currentPage)
    
    else:
        print(f"User and pass combo not found in table")
        print(currentPage)
        return redirect(currentPage)
    
    

#Knapp för att logga ut om man är inloggad och den kommer endast fram ifall man själv är inloggad.
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('index'))

#Form för admin ska kunna besvara kommentarerna för produkterna.
@app.route("/submit_response", methods=["POST"])
def submitresponse():
    adminVariable = json.loads(request.cookies.get("adminReview"))
    response = adminVariable[0]
    reviewID=adminVariable[1]
    #print(reviewVariables)
    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()

    response_query = """UPDATE timsfränadatabas.reviews SET response=%s WHERE reviewID=%s"""

    cursor.execute(response_query, (response, reviewID))

    db.commit()
    cursor.close()
    db.close()

    return redirect(url_for("productInformation"))

#Knapp och form för att ge en kommentar på produkten man är inklickad på. Du behöver även vara inloggad för att lägga kommentaren 
@app.route("/submit_review", methods=["POST"])
def postreview():
    reviewVariables = json.loads(request.cookies.get("reviewValues"))
    userid = session['userid']
    review = reviewVariables[0]
    productid = reviewVariables[1]


    print(reviewVariables)
    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()

    review_query = """INSERT INTO reviews (userid, productid, review) 
    VALUES (%s, %s, %s);"""

    cursor.execute(review_query,(userid,productid,review),)

    db.commit()
    cursor.close()
    db.close()

    return redirect(url_for("productInformation"))

@app.route("/submitRating", methods=["POST"])
def postrating():
    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()

    ratingArray = json.loads(request.cookies.get("ratingArray"))

    rating = ratingArray[0]
    productid = ratingArray[1]
    userid = session['userid']

    fetch_ratings = "INSERT INTO ratings (userid, productid, rating) VALUES (%s,%s,%s)"
    cursor.execute(fetch_ratings,(userid,productid,rating,))
    db.commit()
    cursor.close()
    db.close()

    return redirect(url_for("productInformation"))

    
#Funktion för att skapa användare på hemsidan med användarnamn, mail och lösenord.
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


#Funktion som plockar upp din köphistorik som gjorts med det inloggade kontot.
@app.route("/purchasehistory")
def purchasehistory():
    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()
    userid = session['userid']
    #search_query="""SELECT * FROM timsfränadatabas.orders;"""
    search_query="""SELECT orders.orderid, orders.customeremail, orders.customeradress, orders.customernumber,orders.kvittoorderid, orders.orderdate, orders.status, receipts.productname, receipts.productcost FROM timsfränadatabas.orders JOIN receipts ON orders.kvittoorderid=receipts.kvittoorderid WHERE orders.userid=%s;"""
    cursor.execute(search_query, (userid,))
    result = cursor.fetchall()
    db.commit()
    cursor.close()
    db.close()
    return render_template("purchaseinformation.html", result=result)

@app.route("/adminAddProduct")
def adminAddProduct():
    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()
    userid = session['userid']
    search_query="""SELECT * FROM timsfränadatabas.orders;"""
    data = cursor.execute(search_query)
    result = cursor.fetchall()
    db.commit()
    cursor.close()
    db.close()
    return render_template("adminaddproduct.html", result=result)

@app.route("/adminOrder")
def adminOrder():
    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()
    userid = session['userid']
    search_query="""SELECT orders.kvittoorderid, orders.customeremail, orders.customeradress, orders.customernumber, orders.userid, orders.orderdate, GROUP_CONCAT(receipts.productname) AS productnames, GROUP_CONCAT(receipts.productcost) AS productcosts, orders.status FROM timsfränadatabas.orders JOIN receipts ON orders.kvittoorderid = receipts.kvittoorderid GROUP BY orders.kvittoorderid, orders.customeremail, orders.customeradress, orders.customernumber, orders.userid, orders.orderdate, orders.status;"""
    data = cursor.execute(search_query)
    result = cursor.fetchall()
    db.commit()
    cursor.close()
    db.close()
    return render_template("adminorder.html", result=result)

@app.route("/toggleVisibility")
def toggleVisibility():
    id = json.loads(request.cookies.get("productid"))
    db = mysql.connector.connect(**db_config)
    print(id[0],id[1])
    cursor = db.cursor()
    if (int(id[1])==1):
        print("gick in")
        search_query="""UPDATE timsfränadatabas.products SET visible=0 WHERE productid=%s;"""
    else:
        print("gick in i else")
        search_query="""UPDATE timsfränadatabas.products SET visible=1 WHERE productid=%s;"""
    
    cursor.execute(search_query,(id[0],))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for("index"))

@app.route("/adminConfirm")
def adminConfirmingOrder():
    id = json.loads(request.cookies.get("adminConfirmCookie"))
    print(id)
    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()
    userid = session['userid']
    search_query="UPDATE timsfränadatabas.orders SET status='Shipped' WHERE kvittoorderid=%s;"
    data = cursor.execute(search_query,(id,))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for("adminOrder"))


@app.route("/adminDeny")
def adminDenyOrder():
    id = json.loads(request.cookies.get("adminDenyCookie"))
    print(id)
    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()
    userid = session['userid']
    search_query="UPDATE timsfränadatabas.orders SET status='Denied' WHERE kvittoorderid=%s;"
    data = cursor.execute(search_query,(id,))
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for("adminOrder"))

# Beställnings formulär
@app.route("/order/")
def order():

    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()

    # cartArray = json.loads(request.cookies.get("cartArray"))
    # totalPrice = 0

    # for nycoolvariabelIGEN in cartArray:
    #     totalPrice += int(nycoolvariabelIGEN[2])

    # print(totalPrice)
    userid = session['userid']
    selquery="SELECT productid, COUNT(*) AS item_count FROM cart WHERE customerid=%s GROUP BY productid;"
    data = cursor.execute(selquery,(userid,))
    res = cursor.fetchall()
    temp=res
    print(res)
    amountofproducts = len(res)
    lst=[]
    for i in res:
        forquery="SELECT products.productcost FROM timsfränadatabas.products WHERE productid=%s;"
        cursor.execute(forquery,(i[0],))
        res = cursor.fetchone()
        print("the price of product ",i[0]," is ",res[0], " and the total price is then: ", res[0]*i[1])
        lst.append(res[0]*i[1])

    print(lst)
    totalprice=0

    for i in lst:
        totalprice=totalprice+i

    
    db.commit()
    cursor.close()
    db.close()
    print("order -- temp consists of :",temp," and the type is: ", type(temp), type(temp[0]))
    return render_template("order_form.html", totalPrice=totalprice, cartArray=temp)


@app.route("/submitproduct", methods=["POST"])
def submitproduct():
    print("in submit product")
    productname = request.form.get("productname")
    productcost = request.form.get("productcost")
    productcountryoforigin = request.form.get("productcountryoforigin")
    stock = request.form.get("stock")
    productimagefilepath = "Coming soon"
    productid = random.randint(1, 9999)
    reservedamount=0
    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()

    insert_query = """
        INSERT INTO products (productid, productname, productcost, productimagefilepath, productcountryoforigin, stock, reservedamount)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    
    cursor.execute(insert_query,(productid, productname, productcost, productimagefilepath, productcountryoforigin, stock,reservedamount),
    )

    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for("adminAddProduct"))




@app.route("/submitorder",methods=["POST"])
def submitorder():
    print("in submit order")
    if session['logged_in']:
        userid = session['userid']
    else:
        userid = 0
    
    kvittoorderid = random.randint(1000, 9999)
    cartArray=request.form['cartArray']
    cartArray = json.loads(cartArray)
    customeremail = request.form.get("customeremail")
    customeradress = request.form.get("customeradress")
    customernumber = request.form.get("customerphone")
    
    print(cartArray, len(cartArray), type(cartArray), type(cartArray[0]))

    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()
    
  

    for i in cartArray:
        qry="SELECT * FROM timsfränadatabas.products WHERE productid=%s;"
        cursor.execute(qry,(i[0],))
        result=cursor.fetchone()
        print(result,"for ", i, i[0])
        s=1
        while(s<=i[1]):
            productid = int(result[0])
            productname = result[1]
            priceresult=result[2]
            productimagefilepath = result[3]
            productcountryoforigin = result[4]
            kvittoid = random.randint(1000, 9999)

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
                    priceresult,
                    productimagefilepath,
                    productcountryoforigin,
                ),
            )
            db.commit()
            stock_query = "UPDATE products SET stock=stock-1, reservedAmount=reservedAmount-1 WHERE productid=%s;"
            print("stock&reservedAmount decreased by 1")
            cursor.execute(stock_query, (productid,))
            db.commit()
            s+=1

    orderdate = date.today()
    print(orderdate)
    orderid = random.randint(1000, 9999)
    status = "pending"
    insert_query = """
        INSERT INTO orders (orderid, kvittoorderid, customeremail, customeradress, customernumber, userid, orderdate, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(
        insert_query,
        (orderid, kvittoorderid, customeremail, customeradress, customernumber, userid, orderdate, status),
    )
    db.commit()
    delquery="DELETE FROM cart WHERE customerid=%s;"
    cursor.execute(delquery,(userid,))
    db.commit()
    cursor.close()
    db.close()
    username=session['username']
    return render_template("tack.html", orderid=orderid, username=username)


#När man klickar på checkout så kommer man vidare och får fylla i mailadress adress och telefonnummer
#Denna funtion gör även lite annat som att minska lagret med ett, skapar ordern och skapar ett kvitto.
# @app.route("/submit_order", methods=["POST"])
# def submit_order():
#     if session['logged_in']:
#         userid = session['userid']
#     else:
#         userid = 0
    
#     cartArray = json.loads(request.cookies.get("cartArray"))
#     print("The cart contains:", cartArray)

#     # Kod för att skicka input till databasen
#     try:
#         kvittoorderid = random.randint(1000, 9999)

#         for cartArrayIndex in cartArray:
#             productid = int(cartArrayIndex[0])
#             productname = cartArrayIndex[1]
#             productimagefilepath = cartArrayIndex[3]
#             productcountryoforigin = cartArrayIndex[4]
#             kvittoid = random.randint(1000, 9999)

#             db = mysql.connector.connect(**db_config)
#             cursor = db.cursor()

#             retrieve_query = """SELECT products.productcost	FROM timsfränadatabas.products WHERE products.productid=%s"""
#             cursor.execute(retrieve_query,(productid,))
            

#             result = cursor.fetchone()
#             priceresult=""
#             for i in result:
#                 priceresult+=str(i)
#             priceresult=int(priceresult)
#             print(priceresult)

#             db.commit()
#             cursor.close()
#             db.close()

#             db = mysql.connector.connect(**db_config)
#             cursor = db.cursor()

#             insert_query = """
#                 INSERT INTO `receipts` (kvittoid, kvittoorderid, productid, productname, productcost, productimagefilepath, productcountryoforigin)
#                 VALUES (%s, %s, %s, %s, %s, %s, %s)
#                 """
#             cursor.execute(
#                 insert_query,
#                 (
#                     kvittoid,
#                     kvittoorderid,
#                     productid,
#                     productname,
#                     priceresult,
#                     productimagefilepath,
#                     productcountryoforigin,
#                 ),
#             )
#             print("Passed receipts")
#             db.commit()
#             cursor.close()

#             # functions like a decrease-in-stock for the database
#             db = mysql.connector.connect(**db_config)
#             cursor = db.cursor()
#             stock_query = "UPDATE products SET stock = stock - 1 WHERE productid=%s;"
#             print("stock decreased by 1")
#             cursor.execute(stock_query, (productid,))
#             db.commit()
#             cursor.close()
#             db.close()

#         # Konverterar input från formulär till python variabler
#         # productid = request.form.get('productid')
#         customeremail = request.form.get("customeremail")
#         customeradress = request.form.get("customeradress")
#         customernumber = request.form.get("customerphone")
#         orderdate = date.today()
#         print("this is the orderdate:" + orderdate)

#         # Connection till databasen
#         db = mysql.connector.connect(**db_config)
#         cursor = db.cursor()

#         # Anger ett random orderid, samt säkerställer att productid behandlas som en int
#         orderid = random.randint(1000, 9999)

#         # productid = int(productid)

#         # Skapa ett MySQL commando för att insert input
#         insert_query = """
#             INSERT INTO orders (orderid, kvittoorderid, customeremail, customeradress, customernumber, userid, orderdate)
#             VALUES (%s, %s, %s, %s, %s, %s, %s)
#         """
#         cursor.execute(
#             insert_query,
#             (orderid, kvittoorderid, customeremail, customeradress, customernumber, userid, orderdate),
#         )

#         # Commitar databas ändringarna och stänger db connection för att undvika felaktiga cursors
#         db.commit()
#         cursor.close()
        

#         # db = mysql.connector.connect(**db_config)
#         # cursor = db.cursor()
        
#         # username_query = "SELECT username FROM users WHERE userid=%s;"
#         # cursor.execute(stock_query, (,))
#         # username=cursor.fetchone()
#         # print(username)
#         # db.commit()
#         # cursor.close()

#         db.close()

#         username=session['username']

#         # Går tillbaka till index
#         return render_template("tack.html", orderid=orderid, username=username)

#     except Exception as e:
#         # Fångar problem vid uppladdning till databas
#         print(f"Error submitting order: {e}")
#         return render_template("error.html", error_message="Error submitting order")


# if __name__ == "__main__":
#     app.run(host='0.0.0.0', port=5001, debug=True, threaded=True)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
