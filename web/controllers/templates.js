angular.module('sam').controller('htmlTemplatesController', ['$filter', '$sce','$http','$log', '$location','$compile', '$routeParams', 'User', 'ngTableParams', function($filter, $sce, $http, $log, $location, $compile, $routeParams, User, ngTableParams) {
	
	tmp = this;	

	tiny1 = 	
	{
		selector:'.tiny_sms',
		content_css : "web/css/tinyMce.css",
		height : 300,		
		plugins: ["advlist autolink lists link charmap print preview anchor",
        "searchreplace visualblocks code fullscreen",
        "insertdatetime paste directionality"], 
		toolbar: "undo redo | styleselect | bold italic | link | alignleft aligncenter alignright | ltr rtl"
	};
	
	tiny2 = 	
	{
		selector:'.tiny_mail',
		content_css : "web/css/tinyMce.css",
		height : 300,		
		plugins: ["advlist autolink lists link charmap print preview anchor",
        "searchreplace visualblocks code fullscreen",
        "insertdatetime paste directionality"], 
		toolbar: "undo redo | styleselect | bold italic | link | alignleft aligncenter alignright | ltr rtl"
	};
	
	tiny3 = 	
	{
		selector:'.tiny_letter',
		content_css : "web/css/tinyMce.css",
		height : 300,		
		plugins: ["advlist autolink lists link charmap print preview anchor",
        "searchreplace visualblocks code fullscreen",
        "insertdatetime paste directionality"], 
		toolbar: "undo redo | styleselect | bold italic | link | alignleft aligncenter alignright | ltr rtl"
	};
	
	this.sms_tinyConfig = tiny1;
	this.mail_tinyConfig = tiny2;
	this.letter_tinyConfig = tiny3;
		
	tmp.templates_data = [];
	//a factory which passes paramteres cross controllers
	this.user = User;		
	this.session = {};
	this.showAddForm = false;
	this.watchTemplate = -1;
	this.loading = false;					
	
	tmp.tableParams = new ngTableParams(
		{				
		},
		{
			counts: [],		
			total: this.templates_data.length, // length of data
			getData: function($defer, params) {				
				var orderedData = tmp.orderData(tmp.templates_data);							

				//$defer.resolve(orderedData);
				tmp.templates_data = orderedData;
			}
		}
	);
	
	this.orderData = function(data) {				
		params = this.tableParams;		
		
		var orderedData = params.sorting() ?
									$filter('orderBy')(data, params.orderBy()) :
									data;
			
		return orderedData;
		
	};
	
	this.markTemplate = function(template_id) {
		if (template_id === this.watchTemplate) {
			this.watchTemplate = -1;
		}
		else {
			this.watchTemplate = template_id;
		}
	};
	
	this.isLoading = function() {
		if (this.loading) {
			return "fa-spin";
		}
	};
								
	 			
	//call server to get all templates' info
	this.GetTemplates = function(updated_template) {
		tmp = this;		
		return $http.get('/fetchTemplates_new', {
		params: {		
			updated_template: updated_template
		}
		}).success(function(data) {			
			tmp.templates_data = data.templates;			
		});
	};
	
	this.editTemplate = function(template_details) {		
		this.showAddForm = true;	
		this.session = template_details;		
		this.session.edit = true;		
	};
	
	this.copyTemplate = function(template_details) {
		tmp = this;
		tmp.loading = false; 
		$http.post('/copyTemplate', 
			$.param({
				template_details: JSON.stringify(template_details)		
			}
			)).success(function(data) {				
				tmp.loading = false; 				
				tmp.GetTemplates(data.template_id);				
		});
	};
	
	this.deleteTemplate = function(template_id) {
		if (confirm('אשר מחיקת תבנית') ) {
			tmp = this;	
			//'this' inside the scope of success function will point to $http, so we store the controller pointer into tmp		
			tmp.loading = true; 
			
			$http.post('/deleteTemplate', 
				$.param({
					template_id: template_id			
				}
				)).success(function(data) {				
					tmp.loading = false; 				
					tmp.GetTemplates();				
			});	
		}
	};
	this.addNewTemplate = function(){		
		tmp = this;	
		allow = true;
		
		//if current name appears twice, this means that user tried to edit/add a template to/with a name that exists
		angular.forEach(tmp.templates_data, function(tmpl, index){
			if (tmp.session.name == tmpl.name && tmp.session.template_id != tmpl.template_id){
				allow = false;				
			}
		});	

		if (!allow) {
			alert('תבנית בשם זה קיימת כבר, אנא בחר שם אחר');
			return;
		}				
	
		//'this' inside the scope of success function will point to $http, so we store the controller pointer into tmp		
		tmp.loading = true; 
		
		$http.post('/addNewTemplate', 
			$.param({
				template_details: JSON.stringify(this.session),
				sms_content: this.session.sms_content,
				mail_content: this.session.mail_content,
				mail_subject: this.session.mail_subject,
				letter_content: this.session.letter_content				
			}
			)).success(function(data) {				
				tmp.loading = false; 
				tmp.showAddForm = false;
				tmp.session = {};	
				tmp.GetTemplates(data.template_id);				
		});		
	};
	
	//http://stackoverflow.com/questions/19415394/with-ng-bind-html-unsafe-removed-how-do-i-inject-html
	this.showInnerHtml = function(content){		
		return $sce.trustAsHtml(content);
	};
					
	//call server to get all templates' info
	this.GetTemplates();

}]);