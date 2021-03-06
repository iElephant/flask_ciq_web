from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
import json
import os
import time
from CIQ_parser import *
from CIQ_redis import *

app = Flask(__name__)
app.secret_key = "ormuco"
UPLOAD_FOLDER = 'upload'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
basedir = os.path.abspath(os.path.dirname(__file__))
ALLOWED_EXTENSIONS = set(['xlsx', 'txt'])
my_redis = CiqRedis()


@app.route('/', methods = ['GET', 'POST'])
def home():
    return redirect(url_for('getCustomerList'))


@app.route('/customer_list', methods = ['GET', 'POST'])
def getCustomerList():
    error = None
    m_customers = my_redis.get_set("customer")
    return render_template('customer_list.html', customers = m_customers, error = error)

@app.route('/customer_project_list')
def getCustomerProject():
    error = None
    var_str = request.url.__str__().rsplit('?')
    m_customer = var_str[1].rsplit('=')[1]
    m_projects = my_redis.get_set(m_customer)
    #m_projects = ["vIMS1.6", "ECC"]
    return render_template('customer_project_list.html', customer=m_customer, projects=m_projects, error = error)

@app.route('/customer_node_list')
def getCustomerNode():
    error = None
    var_str = request.url.__str__().rsplit('?')
    m_customer = var_str[1].rsplit('&')[0].rsplit('=')[1]
    m_project = var_str[1].rsplit('&')[1].rsplit('=')[1]
    m_nodes = my_redis.get_set(m_customer + m_project)
    return render_template('customer_node_list.html', customer=m_customer, project=m_project, nodes=m_nodes, error =error)

@app.route('/customer_node_detail')
def getNodeDetail():
    error = None
    var_str = request.url.__str__().rsplit('?')
    m_customer = var_str[1].rsplit('&')[0].rsplit('=')[1]
    m_project = var_str[1].rsplit('&')[1].rsplit('=')[1]
    m_node = var_str[1].rsplit('&')[2].rsplit('=')[1]
    m_attrs = my_redis.get_hash(m_customer + m_project + m_node)
    return render_template('customer_node_detail.html', customer=m_customer, project=m_project, node=m_node, attrs=m_attrs,error =error)

@app.route('/customer_node_modify',methods=['POST'])
def modifyNodeDetail():
    error = None
    var_str = request.url.__str__().rsplit('?')
   
    m_customer = var_str[1].rsplit('&')[0].rsplit('=')[1]
    m_project = var_str[1].rsplit('&')[1].rsplit('=')[1]
    m_node = var_str[1].rsplit('&')[2].rsplit('=')[1]
    m_attrs = my_redis.get_hash(m_customer + m_project + m_node)

    new_attrs ={}

    for key in m_attrs.keys():
        new_attrs[key] = request.form[key]
    my_redis.set_m_hash(new_attrs, m_customer + m_project + m_node)
    return render_template('customer_node_detail.html',customer=m_customer,project=m_project, node=m_node, attrs=new_attrs, error=error)



@app.route('/customer_project_detail')
def getProjectInfo():
    error = None
    var_str = request.url.__str__().rsplit('?')
    m_customer = var_str[1].rsplit('&')[0].rsplit('=')[1]
    m_project = var_str[1].rsplit('&')[1].rsplit('=')[1]
    #mtas = {"oam_vip":"10.0.0.10", "traffic_vip":"10.0.0.11"}
    #sbg = {"mip": "10.0.0.12", "access_ip":"10.0.0.13"}
    #m_ciq = {"mtas": mtas, "sbg":sbg}
    m_ciq = my_redis.get_data(m_customer)[m_project]
    return render_template('customer_project_detail.html', customer=m_customer, project=m_project, ciq=m_ciq, error = error)

@app.route('/alert')
def showAlert(message):
    error = None
    m_message = message
    return render_template('alert.html', message=m_message, error = error)

@app.route('/create_project', methods = ['GET', 'POST'])
def createProject():
    error = None
    if request.method == 'POST':
        m_customer = request.form['customer']
        m_project = request.form['projectName']
        print("fetch customer from db")
        if m_customer == "" or m_project == "":
            error = 'customer and project name cannot be empty. Please try again.'
        elif (my_redis.is_member_set(m_project, m_customer)):
            error = "Project already exists under " + m_customer +", please try again"
            #return render_template('alert.html', message="Project already exists", error=None)
        else:
            return redirect(url_for('upload', customer=m_customer, project=m_project))

    return render_template('create_project.html', error = error)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/upload?customer=<customer>&project=<project>')
def upload(customer, project):
    return render_template('upload.html', customer_var=customer, project_var=project)



@app.route('/api/upload', methods=['POST'], strict_slashes=False)
def api_upload():
    #file_dir = os.path.join(basedir, m_customer)
    print("api_upload")
    var_str = request.url.__str__().rsplit('?')
    m_customer = var_str[1].rsplit('&')[0].rsplit('=')[1]
    m_project = var_str[1].rsplit('&')[1].rsplit('=')[1]
    print(m_customer)
    print(m_project)

    file_dir = os.path.join(basedir, app.config['UPLOAD_FOLDER'])
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)
    f=request.files['myfile']

    if f and allowed_file(f.filename):
        fname=f.filename
        ext = fname.rsplit('.', 1)[1]
        unix_time = int(time.time())
        new_filename = str(unix_time)+'.'+ext
        f.save(os.path.join(file_dir, new_filename))
        
        my_ciq = CIQ_parser(os.path.join(file_dir, new_filename))
        my_ciq.parse_excel()
        my_redis.set_set(m_customer, "customer")
        my_redis.set_set(m_project, m_customer)
        for key,value in my_ciq.nodesConf.items():
            if bool(value):
                my_redis.set_set(key, m_customer+m_project)
                my_redis.set_m_hash(value, m_customer+m_project+key)

        return  render_template("customer_node_list.html", customer=m_customer, project=m_project, nodes=my_ciq.nodesConf.keys())
    else:
        return jsonify({"errno": 1001, "errmsg": "CIQ parse failed"})
#        return jsonify({"filename": f.filename})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
