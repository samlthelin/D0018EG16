from flask import Flask, render_template, g, request, redirect, url_for
import mysql.connector
import random

app = Flask(__name__)

db_config = {
    'host': 'd0018egroup16.cncg2uywo7t4.eu-north-1.rds.amazonaws.com',
    'user': 'admin',
    'password': 'Group161337!',
    'database': 'sammes',
}

db_receipt_config = {
    'host': 'd0018egroup16.cncg2uywo7t4.eu-north-1.rds.amazonaws.com',
    'user': 'admin',
    'password': 'Group161337!',
    'database': 'kvitton',
}

db_receipt_config = {
    'host': 'd0018egroup16.cncg2uywo7t4.eu-north-1.rds.amazonaws.com',
    'user': 'admin',
    'password': 'Group161337!',
    'database': 'sammes',
}

# Function för att connecta till databasen
def get_db():
    if 'db' not in g:
        g.db = mysql.connector.connect(**db_config)
    return g.db

# Function för att få en db cursor
def get_cursor():
    db = get_db()
    if 'cursor' not in g:
        g.cursor = db.cursor()
    return g.cursor

# Stänger ner databasconnection efter varje databas request, då undviker vi att db cursor pekar fel
@app.teardown_appcontext
def close_db(error):
    if 'db' in g:
        g.db.close()

# Frontpage
@app.route('/')
def index():
    # Querya databasen på alla produkter i products
    cursor = get_cursor()
    cursor.execute('SELECT * FROM products;')
    data = cursor.fetchall()

    # Skickar vidare det i en html template
    return render_template('index.html', data=data)

# Beställnings formulär
@app.route('/order/<int:productid>')
def order(productid):
    return render_template('order_form.html', productid=productid)

@app.route('/submit_order', methods=['POST'])
def submit_order():
    # Konverterar input från formulär till python variabler
    productid = request.form.get('productid')
    customeremail = request.form.get('customeremail')
    customeradress = request.form.get('customeradress')
    customerphone = request.form.get('customerphone')

    # Kod för att skicka input till databasen
    try:
        # Connection till databasen
        db = mysql.connector.connect(**db_config)
        cursor = db.cursor()

        #Anger ett random orderid, samt säkerställer att productid behandlas som en int
        orderid = random.randint(1000, 9999)
        orderidtmp = str(orderid)
        receiptreference = 'receipt_'+orderidtmp
        
        productid = int(productid)
        

        # Skapa ett MySQL commando för att insert input
        insert_query = """
            INSERT INTO orders (orderid, receiptreference, customeremail, customeradress, customerphone)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (orderid, receiptreference, customeremail, customeradress, customerphone))

        # Commitar databas ändringarna och stänger db connection för att undvika felaktiga cursors
        db.commit()
        cursor.close()
        db.close()



        # =============== SEARCH COST ===================
        db = mysql.connector.connect(**db_receipt_config)
        cursor = db.cursor()

        searchcost = """SELECT productcost FROM products WHERE productid=%s;"""
        productcost = cursor.execute(searchcost, (productid))

        db.commit()
        cursor.close()
        db.close()
        # =============== SEARCH COST ===================




       
        # =============== INSERT RECEIPT IN TABLE ===================
        db = mysql.connector.connect(**db_receipt_config)
        cursor = db.cursor()

        insert_receipt_query = """
            INSERT INTO receipts (orderid, productid, productcost)
            VALUES (%s, %s, %s)
        """
        cursor.execute(insert_receipt_query, (orderid, productid, productcost))

        db.commit()
        cursor.close()
        db.close()
        # =============== INSERT RECEIPT IN TABLE ===================

        

        # ===================== TIDIGARE MULTI-TABLE CREATION (FUNKAR TYP?) ==========================
        # db = mysql.connector.connect(**db_receipt_config)
        # cursor = db.cursor()

        # receipt_query = """CREATE TABLE `kvitton`.`%s` (
        #     `productid` INT NOT NULL,
        #     `productname` VARCHAR(45) NOT NULL,
        #     `productcost` VARCHAR(45) NOT NULL,
        #     PRIMARY KEY (`productid`))"""
                
        # cursor.execute(receipt_query, (receiptreference))

        # db.commit()
        # cursor.close()
        # db.close()
        # ======================= SLUT PÅ DEN FUNKTIONEN =================================

        #Går tillbaka till index
        return redirect(url_for('index'))

    except Exception as e:
        # Fångar problem vid uppladdning till databas
        print(f"Error submitting order: {e}")
        return render_template('error.html', error_message="Error submitting order")

if __name__ == '__main__':
    app.run(debug=True)


# table för users
    # userid (unikt) ska kunna hämta alla beställningar