angular.module('sam').controller('dashboardController', ['$http', '$log', '$location', '$routeParams','$route', 'User', function($http, $log, $location, $routeParams, $route,User) {
	
	tmp = this;
	
	this.loading = false;		
    
	this.isLoading = function() {
		if (this.loading) {
			return "fa-spin";
		}
	};
	
	//call server to get all Workers' info
	this.GetDashBoardData = function(){		

		tmp = this;	

		//'this' inside the scope of success function will point to $http, so we store the controller pointer into tmp		
		tmp.loading = true; 
		//http://stackoverflow.com/questions/17225088/http-get-parameters-does-not-work
		$http.get('/fetchDashBoardData', {}		
		).success(function(data) {			
			tmp.buildings_count = data.buildings_count;			
			tmp.tenants_count = data.tenants_count;
			tmp.service_count = data.service_count;
			tmp.professionals_count = data.professionals_count;
			tmp.company_logo = data.company_logo;
			tmp.company_web_site = data.company_web_site;
						
			tmp.loading = false;						
		});
	};
	
	this.GetDashBoardData();
		
}]);