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

# Function för att connecta till databasen
def get_db():
    if "db" not in g:
        g.db = mysql.connector.connect(**db_config)
    return g.db


# Function för att få en db cursor
def get_cursor():
    db = get_db()
    if "cursor" not in g:
        g.cursor = db.cursor()
    return g.cursor


# Stänger ner databasconnection efter varje databas request, då undviker vi att db cursor pekar fel
@app.teardown_appcontext
def close_db(error):
    if "db" in g:
        g.db.close()


# Homepage
@app.route("/")
def index():
    # Querya databasen på alla produkter i products
    cursor = get_cursor()
    cursor.execute("SELECT * FROM products;")
    data = cursor.fetchall()
    accountstatus = [0,0,0]

    # Skickar vidare det i en html template
    return render_template("index.html", data=data, accountstatus=accountstatus)


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
        accountstatus = [username, password, 1]

        session['username'] = username
        session['logged_in'] = True

        return redirect(url_for("index"))
    
    else:
        print(f"User and pass combo not found in table")
        accountstatus = [username, password, 0]
        return redirect(url_for("index"))
    

@app.route('/profile')
def profile():
    if 'logged_in' in session and session['logged_in']:
        username = session['username']
        return f"Welcome, {username}"
    else:
        return redirect(url_for("index"))


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

    insert_query = """INSERT INTO `users` (userid, username, password, email, roll)
    VALUES (%s, %s, %s, %s, %s)"""
    cursor.execute(insert_query,(userid,username,password,email,1),)
    
    db.commit()
    cursor.close()
    db.close()

    return redirect(url_for("index"))



# Beställnings formulär
@app.route("/order/")
def order():
    cartArray = json.loads(request.cookies.get("cartArray"))
    return render_template("order_form.html", cartArray=cartArray)





@app.route("/submit_order", methods=["POST"])
def submit_order():
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
                productcountryoforigin,
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
            INSERT INTO orders (orderid, kvittoorderid, customeremail, customeradress, customernumber)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(
            insert_query,
            (orderid, kvittoorderid, customeremail, customeradress, customernumber),
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