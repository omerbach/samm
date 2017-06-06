angular.module('sam').controller('settingsController', ['$filter','$http','$log', '$location','$compile', '$routeParams', 'User', 'ngTableParams', function($filter, $http, $log, $location, $compile, $routeParams, User, ngTableParams) {
	
	tmp = this;
	tmp.staff = [];
	//a factory which passes paramteres cross controllers
	this.user = User;	
	this.excelTypeOf = {1: 'כללי', 2:'מספר'};	
	this.session = {};
	this.showAddForm = false;
	this.loading = false;					
	
	this.tableParams = new ngTableParams(
		{			
		},
		{
			counts: [],		
			total: this.staff.length, // length of data
			getData: function($defer, params) {				
				var orderedData = tmp.orderData(tmp.staff);							

				//$defer.resolve(orderedData);
				tmp.staff = orderedData;
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
	
	this.isLoading = function() {
		if (this.loading) {
			return "fa-spin";
		}
	};
				
			
	this.open_start = function($event) {			
		$event.preventDefault();
		$event.stopPropagation();

		this.opened_start = true;
	 };
	 
	 this.open_end = function($event) {
		$event.preventDefault();
		$event.stopPropagation();

		this.opened_end = true;
	 };
	 			
	//call server to get all settings' info
	this.GetFields = function(updated_field){		

		tmp = this;	

		//'this' inside the scope of success function will point to $http, so we store the controller pointer into tmp		
		tmp.loading = true; 
		//http://stackoverflow.com/questions/17225088/http-get-parameters-does-not-work
		$http.get('/fetchFields', {
		params: {		
			updated_field: updated_field 			
		}
		}).success(function(data) {			
			tmp.staff = tmp.orderData(_.values(data.fields));
			tmp.loading = false;						
		});
	};		
	
	this.editField = function(field_details) {		
		this.showAddForm = true;	
		this.session = field_details;
		this.session.field_type = String(this.session.field_type);
		this.session.edit = true;		
	};
	
	this.deleteField = function(field_id) {
		if (confirm('אשר מחיקת שדה') ) {
			tmp = this;	
			//'this' inside the scope of success function will point to $http, so we store the controller pointer into tmp		
			tmp.loading = true; 
			
			$http.post('/deleteField', 
				$.param({
					field_id: field_id			
				}
				)).success(function(data) {				
					tmp.loading = false; 				
					tmp.GetFields();				
			});	
		}
	};
	this.addNewField = function(){		
		tmp = this;	
		//'this' inside the scope of success function will point to $http, so we store the controller pointer into tmp		
		tmp.loading = true; 
		
		$http.post('/addNewField', 
			$.param({
				field: JSON.stringify(this.session)			
			}
			)).success(function(data) {				
				tmp.loading = false; 
				tmp.showAddForm = false;
				tmp.session = {};	
				tmp.GetFields(data.field_id);				
		});		
	};
	
	this.reset_session = function() {
		this.session = {field_type: '1'};
	};
	
	this.reset_session();	
		
	//call server to get all fields' info
	this.GetFields($routeParams.fieldId);

}]);