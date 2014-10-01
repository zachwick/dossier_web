'''
The main server application
This file sets the URL routes and handles all HTTP requests

Copyright 2014 zachwick <zach@zachwick.com>
Licensed under the AGPLv3 or later

'''

import web
import model
import json
import csv
import hashlib
import os

'''
 If web.config.debug is not explicitly set to False, sessions with not work.
 That is, you will be unable to log in or out.
'''
web.config.debug = False

'''
 URL Mapping/Routing
 NB: Unless the Apache2/Nginx server is dealing with omitted trailing slashes
     the routes themselves have to handle them. Even if the Apache2/Nginx 
     server is handling trailing slashes, it won't hurt to have both versions
     of the routes defined here just in case something gets weird.
     This is only a big issue for login, logout, and upload. The other routes
      are hit via created URLs from Backbone, and are pretty compatable.
'''
urls = (
    # "Root" of the entire web app and API
    '/',                                'Index',

    # A POST of a correct username/passwork combination to these routes will
    # log a user in and create new session.
    '/login/',                          'Login',
    '/login',                           'Login',

    # A POST to either of these routes will log out a user by killing their
    # session
    '/logout',                          'Logout',
    '/logout/',                         'Logout',

    # The API endpoint for creating, modifying, and/or deleting users
    '/users/',                          'Users',

    # This API endpoint if for listing all user records in the DB and is
    # only available to users with a privilege level of 2
    '/allusers/',                       'AllUsers',

    # This API endpoint is for interacting with a single WSN node identified by
    # the supplied id.
    # NB: This 'id' is the database id, not the BackboneJS model's cid property.
    '/nodes/(\d+)',                     'SingleNode',

    # This API endpoint is for either GET-ting all nodes, or POST-ing a new
    # new only.
    '/nodes/',                          'Nodes',

    # This API endpoint is for interacting with a single site identified byt the
    # supplied id.
    # NB: This 'id' is the database id, not the BackboneJS model's cid property.
    '/sites/(\d+)',                     'SingleSite',

    # This API is for either GET-ting all sites, or POST-ing a new site only.
    '/sites/',                          'Sites',

    # This API endpoint is for interacting with a single datapoint identified by
    # the supplied id.
    # NB: This 'id' is the database id, not the BackboneJS model's cid property.
    #'/datapoints/(\d+)',                'SingleDatapoint',

    # This API endpoint is for either GET-ting all datapoints, or POST-ing a new
    # datapoint only.
    '/datapoints/',                     'Datapoints',

    # This API endpoint is for devices authenticating in order to get a session
    # token that they then use to send data to the /datapoints/ endpoint
    '/auth/',                           'Auth',
)

'''
Templates
Look in a folder named "templates" for our webpy HTML templates, and use a file
base.html as a base template for all views that webpy creates.
NB: These are templates for the HTML that the webpy application returns to
    connected clients. They are not the BackboneJS templates. The BackboneJS
    templates are defined in the index.html webpy template.
'''
render = web.template.render ("templates",base="base")

'''
Application
Create the webpy application.
'''
app = web.application (urls, globals())

'''
Sessions
We are initially going to store user sessions "on disk" instead of in a
database. If using a database, the table needs to have a particular structure,
and I just needed something that worked quickly without too much tweaking.
'''
store = web.session.DiskStore('sessions')
# When we create a new session, it is initially populated with the structure that
# you see below.
session = web.session.Session(app, store,
                              initializer={"login":0, 
                                           "privilege":0,
                                           "username":"",
                                           "id":0})

class Index:
    def GET(self):
        '''
        Show the base index.html page if the user has a valid session, and
        if there is not a valid session, punt the user to the login page.
        '''
        if session.login == 1:
            return render.index()
        else:
            return render.login()

class Users:
    def PUT(self):
        # Add a new user
        data = json.loads(web.data())
        data['password'] = hashlib.md5(data['password']).hexdigest()
        new_id = model.new_user(data)
        # Don't pass the MD5-ed password back, this would be a big security hole
        data = [{
            "username": data['username'],
            "email": data['email'],
            "privilege": data['privilege'], # TODO: Check this privilege
            "id": new_id
        }]

        '''
        You are going to see the next three lines quite a bit. We use the response
        headers to make browsers play nicely with us passing back JSON data. We
        the json.dumps() function to serialize our data dictionary into a JSON
        structure. If you are getting python errors when trying to use json.dumps
        you probably have a cyclic reference in what you are trying to serialize.
        '''
        web.header("Content-Type","application/json")
        web.header("Cache-Control","no-cache")
        return json.dumps(data) 

    def GET(self):
        '''
        Get all of the information about the currently logged in user.
        But DO NOT pass back the MD5-ed password or the plaintext password
        '''
        data = {
            "username": session.username,
            "email": session.email,
            "privilege": session.privilege,
            "id": session.id
        }

        web.header("Content-Type", "application/json")
        web.header("Cache-Control", "no-cache")
        return json.dumps(data)

class AllUsers:
    def GET(self):
        '''
        Get a list of _all_ users that exist in the DB.
        This method is only available to the super admin user
        '''
        if session.privilege == 2:
            self.users = model.get_users()
            data = []
            for user in self.users:
                data.append({
                    "email": user.email,
                    "id": user.id,
                    "username": user.username,
                    "privilege": user.privilege
                })
            
            web.header("Content-Type", "application/json")
            web.header("Cache-Control", "no-cache")
            return json.dumps(data)

class Auth:
    def POST(self):
        data = json.loads(web.data())
        pass_sha256 = hashlib.md5(data.password).hexdigest()
        match = model.check_device_auth_values(data.username, data.password, data.macaddr)
        if match:
            return_data = []
            return_data.append({
                "session_token": hashlib.md5(os.urandom(256)).hexdigest()
            })
            session_created = model.set_device_session(return_data.session_token, data.macaddr)
            if session_created:
                web.header("Content-Type", "application/json")
                web.header("Cache-Control", "no-cache")
                return json.dumps(return_data)


class Login:
    def POST(self):
        data = web.input(user="",passwd="")
        '''
        Using an unsalted MD5 hash for passwords is probably not a good idea.
        This should probably be a salted SHA256 hash instead.
        NB: When changing to SHA256, the DB structure will need to be modified
            from passwords being 32 long to 64 long.
        '''
        pass_md5 = hashlib.md5(data.passwd).hexdigest()
        match = model.check_login_values(data.user, pass_md5)
        if match:
            # Start a new session for this user
            session.login = 1
            users = model.get_logged_in_user(data.user, pass_md5)
            for user in users:
                session.privilege = user.privilege
                session.username  = user.username
                session.email     = user.email
                session.id        = user.id

        # We rely on the redirect in Index.GET to handle any login errors
        web.seeother("/")

class Logout:
    def GET(self):
        '''
        Kill the session, and redirect to the root page which takes over
        and redirects elsewhere.
        '''
        session.login = 0
        web.seeother("/")

class Nodes:
    def PUT(self):
        data = json.loads(web.data())
        data['password'] = hashlib.md5(data['password']).hexdigest()
        new_id = model.new_node(data)
        data = [{
            "macaddr": data['macaddr'],
            "well_id": data['well_id'],
            "site_id": data['site_id'],
            "id": new_id,
            "lat": data['lat'],
            "lon": data['lon']
        }]

        web.header("Content-Type","application/json")
        web.header("Cache-Control","no-cache")
        return json.dumps(data) 


class SingleNode:
    def GET(self, id):
        '''
        GET all of the data about a single particular WSN node
        '''
        self.nodes = model.get_node(id)
        self.datapoints = model.get_datapoints_for_node(id)
        data = []

        '''
        This for loop first constructs all of the Datapoint data packets.
        It then constructs the node data packet

        Does this for loop look familiar?

        "Quod crebro videt non miratur, etiamsi cur fiat nescit. Quod ante non
        vidit, id si evenerit, ostentum esse censet."
           - Cicero (De Divinatione, II. 22)

        Translated in case you don't speak Latin:
        "A man does not wonder at what he sees frequently, even though he be
        ignorant of the reason. If anything happens which he has not seen before,
        he calls it a prodigy."
        '''
        for node in self.nodes:
            datapoints = []
            for datapoint in self.datapoints:
                if datapoint.node_id == node.id:
                    datapoints.append({
                        "id": datapoint.id,
                        "node_id": datapoint.node_id,
                        "methane": datapoint.methane,
                        "co2": datapoint.co2,
                        "temp": datapoint.temp,
                        "pressure": datapoint.pressure,
                        "amb_temp": datapoint.amb_temp,
                        "pipe_temp": datapoint.pipe_temp,
                        "humidity": datapoint.humidity,
                        "vbatt": datapoint.vbatt,
                        "timestamp": str(datapoint.timestamp)
                    })
            data.append({
                "id": id,
                "lat": node.lat,
                "lon": node.lon,
                "macaddr": node.macaddr,
                "well_id": node.well_id,
                "datapoints": datapoints,
            })

        '''
        Ensure that the response headers are correct. Told you that you would
        see these lines again.

        These lines should be familiar, so how about another quote about
        familiarity, in english this time?

        "And sweets grown common lose their dear delight."
           - William Shakespear (Sonnet CII)

        If you had to look up both of those quotes to know who first said them,
        you should step away from the keyboard and expand your horizons outside
        of pixels, packets, and the beauty of the BAUD.
        '''
        web.header("Content-Type", "application/json")
        web.header("Cache-Control", "no-cache")
        return json.dumps(data[0])

    def PUT(self, id):
        '''
        Update an existing node. This functionality doesn't yet exist in the
        JavaScript web app, but with a fancy cURL call (or an AJAX call) you
        could force it to work.
        '''
        data = json.loads(web.data())
        '''
        The "magic" in this method is mostly in the 'update_node' method
        from the 'model' module. That isn't to say that there isn't magic
        elsewhere in here; I mean, just look at what you are doing - you are
        hitting some keys to connect some circuits to draw pixels on a screen
        that some how are stored in a way that can be translated into "on's" 
        and "off's" that get run elsewhere. If that isn't magic, I don't know
        what is.
        '''
        model.update_node(data)

        '''
        Here we just return the data that sent to the server. This is really
        just done for completness with regard to the HTTP verb.
        '''
        data = [{
            # TODO: Other node values here
            "id":  data['id'],
            "lat": data['lat'],
            "lon": data['lon'],
            "macaddr": data['macaddr'],
            "well_id": data['well_id']
        }]

        '''
        Guess what is going on here?
        Instead of having to repeat these same lines all over, there is
        probably a clever way to only write them once and then just reuse them
        over and over, but I haven't spent the time investigating that option.
        A wholesale 'Content-Type' header of 'application/json' would be overkill
        though since we do want to return (X)HTML from some routes.
        '''
        web.header("Content-Type", "application/json")
        web.header("Cache-Control", "no-cache")
        return json.dumps(data)

    def DELETE(self, id):
        '''
        Hitting this method removes the related node record from the database.
        Unless MySQL is set up to keep transaction logs, this will be irreversible.
        That being so, it is probably a good idea to put a confirmation dialog for
        the delete functionality in the JavaScript web app.
        '''
        model.delete_node(id)

class SingleSite:
    def GET(self, id):
        '''
        Get all of the data (site data and all site nodes) about a single site.
        Note that we don't return any Datpoints in this call. Datapoints are only
        accessible via the Node that contains them.
        '''
        self.sites = model.get_site(id)
        self.nodes = model.get_nodes_for_site(id)
        data = []

        for site in self.sites:
            nodes = []
            for node in self.nodes:
                nodes.append({
                    "id": node.id,
                    "lat": node.lat,
                    "lon": node.lon,
                    "macaddr": node.macaddr,
                    "well_id": node.well_id
                })

            data.append({
                # TODO: add other site values here
                "id":   site.id,
                "name": site.name,
                "nodes": nodes
            })

        '''
        The next set of lines should be pretty self-evident by now - JSONify the
        data and set the response headers.
        '''
        web.header("Content-Type", "application/json")
        web.header("Cache-Control", "no-cache")
        return json.dumps(data[0])

    def PUT(self, id):
        '''
        Update an existing site. This functionality needs implemented
        '''

    def DELETE(self, id):
        '''
        Hitting this method removes the related site record from the database.
        Unless MySQL is set up to keep transaction logs, this will be irreversible.
        That being so, it is probably a good idea to put a confirmation dialog for
        the delete functionality in the JavaScript web app.
        '''
        model.delete_site(id)

class Sites:
    def GET(self):
        '''
        GET a list of all sites that the logged in user has access to.
        This method is very straight forward, and for anybody who has been
        reading along since the beginning, it should look pretty familiar.
        '''
        if session.privilege == 2:
            self.sites = model.get_sites()
        else:
            self.sites = model.get_sites_for_user(session.id)

        data = []
        for site in self.sites:
            data.append({
                "id": site.id,
                "name": site.name
            })

        web.header("Content-Type", "application/json")
        web.header("Cache-Control", "no-cache")
        return json.dumps(data)

    def POST(self):
        '''
        Add a new site
        '''
        data = json.loads(web.data())
        #data['user_id'] = session.id
        new_id = model.new_site(data)
        data = [{
            "id": new_id,
            "name": str(data['name'])
        }]

        web.header("Content-Type", "application/json")
        web.header("Cache-Control", "no-cache")
        return json.dumps(data)

class Datapoints:
    def POST(self):
        '''
        Add a new datapoint from the Coordinator/Gateway
        '''
        data = json.loads(web.data())
        new_id = model.new_datapoint(data)
        '''
        We don't really care about returning anything to the
        coordinator/gateway, so don't do any kind of returning
        '''
    
if __name__ == '__main__':
    app.run()
