angular.module('sam').controller('groupSmsController', ['$http', '$log', '$location', '$routeParams','$route', 'User', function($http, $log, $location, $routeParams, $route,User) {
	
	tmp = this;
	this.showSendSummery = false;
	this.credit = 1;
	//a factory which passes paramteres cross controllers
	this.user = User;	

	this.MultiTypeElements = function(chosen_entities){			
		tmp = this;			
		tmp.loading = true;
		
		$http.get('/fetchMultiTypeElements', {
		params: {		
			include_specific_buildings: true			
		}
		}).success(function(data) {				
			tmp.entities = data.entities;			
			if (!_.isUndefined(chosen_entities) && chosen_entities.length) {				
				tmp.chosenEntities = chosen_entities.split(',');				
			}
				
			tmp.loading = false;				
		});
	};
	
	this.GetSmsCredit = function(){			
		tmp = this;			
		tmp.loading = true;
		
		$http.get('/fetchSmsCredit', {
		params: {}
		}).success(function(data) {				
			tmp.credit = data.credit;
			tmp.loading = false;				
		});
	};
	
	this.loading = false;		
    
	this.isLoading = function() {
		if (this.loading) {
			return "fa-spin";
		}
	};
	
	this.refresh = function(){		
		this.MultiTypeElements();
		this.clearSms();
	};
	
	this.clearSms = function() {
		this.sms_content = "";		
		this.chosenEntities = [];
		this.worker_id = "";
		this.showSendSummery = false;
	};
	this.sendGroupSms = function(){
		tmp.loading = true;		
		tmp = this;
		$http.get('/sendGroupSms', {
		params: {		
			recepients: JSON.stringify(tmp.chosenEntities),
			sms_body: tmp.sms_content,
			worker_id: tmp.worker_id,			
		}
		}).success(function(data) {				
			tmp.loading = false;
			tmp.clearSms();
			tmp.showSendSummery = true;
		}).
		error(function(data) {
			
		});
	};	
	
	//call server to get all Workers' info
	this.GetWorkers = function(){		
		tmp = this;	
		//'this' inside the scope of success function will point to $http, so we store the controller pointer into tmp		
		tmp.loading = true; 
		//http://stackoverflow.com/questions/17225088/http-get-parameters-does-not-work
		$http.get('/fetchWorkers', {
		params: {}
		}).success(function(data) {			
			tmp.workerOf = data.workers;
			tmp.availableWorkers = _.values(tmp.workerOf);			
			
			tmp.loading = false;						
		});
	};
		
	this.GetWorkers();
	this.clearSms();
	this.MultiTypeElements($routeParams.entities);
	this.GetSmsCredit();
	
		
}]);