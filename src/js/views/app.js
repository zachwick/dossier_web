var AppView = Backbone.View.extend({
	// A Sizzle/jQuery selector for the DOM element that an AppView object
	// uses to interact with the DOM
	el: "#app-container",

	// Note that this is a fancy way to wrap around the UnderscoreJS template
	// function. We will use this AppView.template function to manipulate the
	// DOM
	template: function() {
		return _.template($("#app-template").html());
	},

	// Define any UI events and the functions that are bound to them
	events: {
		'click .logout-button': 'doLogout'
	},

	// This method directs the browser to '/logout' which logs out the user
	// and then triggers the whole create session/login flow.
	doLogout: function(e) {
		window.location = "/logout";
	},

	// This AppView.initialize function is called whenever we create a new
	// AppView object; Think of it kind of like a C++ constructor.
	initialize: function(options) {
		// The a Backbone collection of Vehicle models
		//this.vehicles = new Vehicles();
		this.sites = new Sites();

		this.user = new User();

		// When we 'add' or 'remove' from our collection of sites, call the
		// AppView.render method. Look at the BackboneJS docs for more info.
		this.listenTo(this.sites, 'add remove', this.render);

		// When we 'change' the user model, re-render
		this.listenTo(this.user, 'change', this.render);

		// Call the AppView.render method to initialize the DOM
		this.render();

		// Make sure that our collection of Site objects is up to date.
		this.sites.fetch();

		// Make sure that our user object reflects the currently logged-in user
		this.user.fetch();

		// Ensure that 'this' plays nicely inside each of our AppView's methods
		_.bindAll(this,
		          "addOneSite",
		          "addAllSites",
		          "newSite",
		          "populateDataTable",
		          "render"
		         );
	},

	// Create a new SiteView and add it to the displayed list of sites
	// @param site - A Site model to create a view for.
	addOneSite: function(site) {
		var view = new SiteView({ model: site });
		this.$("#site-list").append(view.render().el);
	},

	// Create a new SiteView for each Site model in our sites
	// collection. We do this by calling AppView.addOneSite for each model.
	addAllSites: function() {
		this.sites.each(this.addOneSite, this);
	},

	newUser: function(e) {
		e.stopPropagation();
		e.preventDefault();

		if (this.$("input[name='password']").val() == this.$("input[name='confirm']").val()) {
			var newUser = new User({
				username: this.$("input[name='username']").val(),
				email: this.$("input[name='email']").val(),
				password: this.$("input[name='password']").val(),
				privilege: this.$("#add-user-form > option:selected").val()
			});
			newUser.save();
		}
	},

	// Add a new site to the database
	// @param e - the Event object that triggered AppView.newVehicle being
	//            called.
	newSite: function(e) {
		e.stopPropagation();
		e.preventDefault();

		var newSite = new Site({
			name: this.$("input[name='name']").val()
		});
		// Don't allow empty inputs to be submitted
		// TODO: implement some kind of error messaging.
		if (newSite.get("name") != "") {

			// This is the actual AJAX request that saves the new Vehicle
			newSite.save({},{
				// The 'success' handler only fires on non-error codes
				success: _.bind(function(model,response,collection) {
					// Simply adding the new Vehicle model to our collection
					// is enough because then the event bindings that were
					// defined in AppView.initialize take over
					this.sites.add(model);
				},this)
			});
		}
	},
	
	// This method populates the data table with all of the selected nodes'
	// data
	populateDataTable: function() {
		this.$(".data-table-tbody").empty();

		this.sites.each(_.bind(function(site) {
			if (site.get("display")) {
				if (site.get("nodes").length) {
					site.get("nodes").each(_.bind(function(node) {
						if (node.get("display")) {
							if (node.get("datapoints").length && typeof node.get("datapoints").each !== "undefined") {
								node.get("datapoints").each(this.addDataTableEntry, this);
							}
						}
					},this));
				}
			}
		},this));
	},

	// This method takes a Datapoint model and creates the corresponding data
	// table record.
	addDataTableEntry: function(datapoint) {
		var view = new DatapointView({ model: datapoint });
		// TODO: use jQuery to add the new DatapointView to the data table
		this.$(".data-table-tbody").append(view.render().el);
	},

	// This method is the access point of all DOM manipulation by the
	// AppView object
	render: function() {
		this.$el.html(this.template()({privilege: this.user.get("privilege")}));
		this.addAllSites();
	}
});
