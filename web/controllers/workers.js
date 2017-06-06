angular.module('sam').controller('workersController', ['$filter','$http','$log', '$location','$compile', '$routeParams', 'User', 'ngTableParams', function($filter, $http, $log, $location, $compile, $routeParams, User, ngTableParams) {
	
	tmp = this;
	tmp.staff = [];
	//a factory which passes paramteres cross controllers
	this.user = User;	
	
	if (_.isUndefined(this.user.start_dt)) {
		//start at the first day of the year at midnight and 1 minute and 16 seconds
		this.user.start_dt = new Date(new Date().getFullYear() -1, 0, 1, 16);
	}
	
	if (_.isUndefined(this.user.finish_dt)) {
		//end date defaults for today
		this.user.finish_dt = new Date();	
	}
		
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
	 			
	//call server to get all Workers' info
	this.GetWorkers = function(updated_worker){		

		tmp = this;	

		//'this' inside the scope of success function will point to $http, so we store the controller pointer into tmp		
		tmp.loading = true; 
		//http://stackoverflow.com/questions/17225088/http-get-parameters-does-not-work
		$http.get('/fetchWorkers', {
		params: {		
			updated_worker: updated_worker,
			start_date: $filter('date')(tmp.user.start_dt, 'yyyy-MM-dd' ),
			end_date: $filter('date')(tmp.user.finish_dt, 'yyyy-MM-dd')
		}
		}).success(function(data) {			
			tmp.staff = tmp.orderData(_.values(data.workers));
			tmp.loading = false;						
		});
	};		
	
	this.editWorker = function(worker_details) {
		this.showAddForm = true;	
		this.session = worker_details;
		this.session.edit = true;		
	};
	
	this.deleteWorker = function(worker_id) {
		if (confirm('אשר מחיקת עובד') ) {
			tmp = this;	
			//'this' inside the scope of success function will point to $http, so we store the controller pointer into tmp		
			tmp.loading = true; 
			
			$http.post('/deleteWorker', 
				$.param({
					worker_id: worker_id			
				}
				)).success(function(data) {				
					tmp.loading = false; 				
					tmp.GetWorkers();				
			});	
		}
	};
	this.addNewWorker = function(){		
		tmp = this;	
		//'this' inside the scope of success function will point to $http, so we store the controller pointer into tmp		
		tmp.loading = true; 
		
		$http.post('/addNewWorker', 
			$.param({
				worker: JSON.stringify(this.session)			
			}
			)).success(function(data) {				
				tmp.loading = false; 
				tmp.showAddForm = false;
				tmp.session = {};	
				tmp.GetWorkers(data.worker_id);				
		});		
	};
	
			
	//call server to get all Workers' info
	this.GetWorkers($routeParams.workerId);

}]);