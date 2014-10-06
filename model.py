import web

db = web.database (dbn="mysql", db="dossier", user="root", passwd="Fritz")

### Site DB/Table Methods

def get_sites():
    return db.select ("Site", order="id")

def get_sites_for_user(userid):
    return db.select ("Site", where="user_id=$userid", vars=locals())

def get_site(id):
    return db.select ("Site", where="id=$id", vars=locals())

def new_site(data):
    name = data['name']
    user_id = data['user_id']
    
    new_id = db.insert("Site",
                       name=name,
                       user_id=user_id)
    return new_id

def delete_site(id):
    db.delete("Site", where="id=$id", vars=locals())

### Node DB/Table Methods

def get_nodes():
    return db.select ("Node", order="id")
    
def get_node(id):
    return db.select ("Node", where="id=$id", vars=locals())

def get_nodes_for_site(site_id):
    return db.select ("Node", where="site_id=$site_id", vars=locals())

def new_node(data):
    new_id = db.insert("Node",
                       macaddr=data['macaddr'],
                       well_id=data['well_id'],
                       lat=data['lat'],
                       lon=data['lon'],
                       username=data['username'],
                       password=data['password'],
                       site_id=data['site_id'])
    return new_id

def delete_node(id):
    db.delete ("Node", where="id=$id", vars=locals())

### Datapoint DB/Table Methods

def get_datapoints():
    return db.select ("Datapoint", order="id")

def get_datapoints_for_node(node_id):
    return db.select ("Datapoint", where="node_id=$node_id", vars=locals())

def new_datapoint(data):
    macaddr  = data['macaddr']
    '''
    Get the node_id that corresponds to the given macaddr
    '''
    node_id_list  = db.select ("Node", where="macaddr=$macaddr",vars=locals())
    for node in node_id_list:
	node_id=node.id	
    '''
    db.select() returns a container.
    Each line contains a dictionary that the db has returned.
    Use var.value rather than var['value']. NR
    '''	


    methane  = data['methane']
    co2      = data['co2']
    temp     = data['temp']
    pressure = data['pressure']
    amb_temp = data['amb_temp']
    pipe_temp = data['pipe_temp']
    humidity = data['humidity']
    timestamp = data['timestamp']
    vbatt = data['vbatt']

    new_id = db.insert ("Datapoint",
                        node_id=node_id,
                        methane=methane,
                        co2=co2,
                        temp=temp,
                        pressure=pressure,
                        amb_temp=amb_temp,
                        pipe_temp=pipe_temp,
                        humidity=humidity,
                        vbatt=vbatt,
                        timestamp=timestamp)

    return new_id

### Device Auth DB/Table Methods
def check_device_auth_values(user, passwd, macaddr):
    nodes = db.select("Node", where="macaddr=$macaddr AND username=$user AND password=$passwd",vars=locals())
    if len(nodes) > 0:
        return True
    else:
        return False

def set_device_session(token, macaddr):
    nodes = db.update("Node", where="macaddr=$macaddr", session = token, vars=locals())
    if nodes == 1:
        return True
    else:
        return False

### User DB/Table Methods

def get_users():
    return db.select ("User", order="id")

def new_user(data):
    username  = data['username']
    email     = data['email']
    privilege = data['privilege']
    password  = data['password']

    new_id = db.insert ("User",
                        username=username,
                        email=email,
                        privilege=privilege,
                        password=password)

    return new_id

def check_login_values(user, passwd):
    users = db.select("User", where="username=$user AND password=$passwd",
                      vars=locals())
    if len(users) > 0:
        return True
    else:
        return False

def get_logged_in_user(user, passwd):
    return db.select("User", where="username=$user AND password=$passwd",
                     vars=locals())
