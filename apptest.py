from flask import Flask, render_template, request
import mysql.connector

app = Flask(__name__)
db_config = {
    'host': 'd0018egroup16.cncg2uywo7t4.eu-north-1.rds.amazonaws.com',
    'user': 'admin',
    'password': 'Group161337!',
    'database': 'humans',
}

def create_connection():
    return mysql.connector.connect(**db_config)
@app.route('/')


# def get_data():
#     try: 
#         connection = create_connection()
#         cursor = connection.cursor()
#         query = "SHOW TABLES;"
#         cursor.execute(query)
#         data = cursor.fetchall()
#         cursor.close()
#         connection.close()
#         return render_template('index.html', data = data)
#     except Exception as e:
#         return f"An error occured: {str(e)}"

@app.route('/')
def homepage():
    return render_template('index.html')

@app.route('/index2')
def page2():
    return render_template('index2.html')

@app.route('/execute_function')
def execute_function():
    try:
        result = "potatos"
        return result

    except Exception as e:
        return 

@app.route('/execute_query', methods=['POST'])
def execute_query():
    query = request.form['query']
    result = execute_sql_query(query)

    return f"Query result: {result}"

def execute_sql_query(query):
    return f"Executing query: {query}"


if __name__ == "__main__":
    app.run(debug=True)