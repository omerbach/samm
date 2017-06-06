angular.module('sam').controller('mainController', ['$scope', '$filter', '$http','$log', '$location', '$routeParams', 'User', 'ngTableParams', function($scope, $filter, $http, $log, $location, $routeParams, User, ngTableParams){		
	//call server to get all debt types
	this.GetDebtTypes = function(){		

		tmp = this;	

		//'this' inside the scope of success function will point to $http, so we store the controller pointer into tmp		
		tmp.loading = true; 
		//http://stackoverflow.com/questions/17225088/http-get-parameters-does-not-work
		$http.get('/fetchDebtTypes', {		
		}).success(function(data) {			
			tmp.user.debt_types = data.debt_types;
			tmp.user.debt_type = tmp.user.debt_types[0];	
			tmp.loading = false;	
			tmp.GetBuildings($routeParams.buildingId);	
		});
	};
	
	tmp = this;
	this.elements = [];
	this.distinct_nick_names = [];
	this.visibleBuildings = [];
	this.building_files = [];
	this.user = User;				
	
	if (_.isUndefined(this.user.start_dt)) {
		//start at the first day of the year at midnight and 1 minute and 16 seconds
		this.user.start_dt = new Date(new Date().getFullYear() - 1, 0, 1, 16);		
	}
	
	if (_.isUndefined(this.user.finish_dt)) {
		//end date defaults for today
		this.user.finish_dt = new Date();	
	}			
	
	this.filterOptions = {
		filterText: ""
	};

	this.loading = false;	
	this.isLoading = function() {
		if (this.loading) {
			return "fa-spin";
		}
	}
	
	this.column_building_name = true;
	this.column_nick_name = false;	
	this.column_based_on_file = false;
	this.column_updated = true;
	this.column_debt = true;
	this.column_percentage = true;	
	this.showColumnPanel = false;
	
	this.masterCheckBoxState = 1; //1- uncheck, 2-partial, 3-all		
	this.total_buildings = 0;
	
	this.buildingDescription = "";		
		
	this.tableParams = new ngTableParams(
		{
			//initial sorting by a decreasing date
			sorting: {percent: "desc"}
		},
		{
			counts: [],		
			total: this.elements.length, // length of data
			getData: function($defer, params) {				
				var orderedData = tmp.orderData(tmp.elements);							
				
				tmp.elements = orderedData;
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
	
	this.UpdateBuildingDescription = function() {
		
		if (this.visibleBuildings.length > 0) {
			if (this.visibleBuildings.length == 1) {					
					this.buildingDescription = this.visibleBuildings[0].name;				
			}
			else {
				this.buildingDescription = this.visibleBuildings.length + ' ' + 'בניינים';	
			}	
		}
		return this.buildingDescription;
	};
	
	this.UpdateBuildingsMetaData = function(delta) {
		this.total_buildings += delta;
		if (!this.total_buildings) {
				this.masterCheckBoxState = 1;
			}
		else if (this.total_buildings == _.keys(buildings_data).length) {
			this.masterCheckBoxState = 3;
		}
		else {
			this.masterCheckBoxState = 2;
		}						
	};		
	
	this.UpdateBuildings = function(new_buildings) {
		tmp = this;				
		tmp.total_buildings = 0;
		buildings_data = tmp.orderData(new_buildings);
		nick_names_dict = {};
		distinct_nick_names = [];		
		
		//remove previous watches
		angular.forEach(tmp.elements, function(building, index){
			building['listener']();
		});								
		
		angular.forEach(buildings_data, function(building, index){
			
			if (buildings_data[index].nick_name) {
				$log.log(buildings_data[index].nick_name);
				nick_names_dict[buildings_data[index].nick_name] = 'bla';
			}
			
			//when fetching the buildings_data, each row which is selected from the beginning will not
			if (buildings_data[index].building_selected) {				
				tmp.UpdateBuildingsMetaData(1);				
			}
			
			
			//add watchers for all buildings to track changes in row selections (this is due to the fact that angular does not 
			//trigget on change methods when model is changed)				
			listener = $scope.$watch(
			//watchExpression
			function(){
				return buildings_data[index];
			}, 
			//listener
			function(nv, ov) {						
				//row check box has changed
				if (nv.building_selected != ov.building_selected) {					
					//update total of buildings selected
					delta = 1;
					if (!nv.building_selected) {
						delta *= -1;
					}		
					
					tmp.UpdateBuildingsMetaData(delta);
				}
			},
			//objectEquality
			true);	
			
			//http://stackoverflow.com/questions/14957614/angular-js-clear-watch
			//store the return value from each watch. this is the function which deregister the object
			building['listener'] = listener;
		});
		
		tmp.distinct_nick_names = _.keys(nick_names_dict);		
		tmp.elements = buildings_data;		
		tmp.loading = false;		
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

	
	this.masterCheckBoxClick = function($event){		
		if (this.masterCheckBoxState == 1){			
			this.selectAllVisibleBuildings();
		}
		else if (this.masterCheckBoxState == 3){			
			this.clearSelections();	
		}
		else if (this.masterCheckBoxState == 2){			
			this.clearSelections();	
		}
		$event.stopPropagation();		
	};
	
	this.showBuildingsData = function() {
		chosenBuildings = [];
		
		$.each(this.elements, function(index, data){				
			if (data.building_selected) {
				chosenBuildings.push(data.id);				
			}			
		});	
				
		$location.url( '/tenants?buildingIds='+chosenBuildings);
	};
	
	this.clearSelections = function(){											
		tmp = this;
		angular.forEach(this.elements, function(data, index){							
			data.building_selected = false;			
		});		
	};
	
	this.selectAllVisibleBuildings = function() {
		tmp = this;		
		this.clearSelections();	
			
		angular.forEach(this.visibleBuildings, function(data, index){							
			data.building_selected = true;			
		});				
	};
	
	this.selectBuildingsByNickName = function(nick_name) {
		tmp = this;		
		this.clearSelections();	
		
		angular.forEach(this.visibleBuildings, function(data, index){	
			if (data.nick_name == nick_name){
				data.building_selected = true;
			}
		});		
	};
	
	this.guessBuildingNickName = function(val) {		
		return $http.get('/guessBuildingNickName', {
			params: {
			name: val
			}
		}).then(function(res) {		
			return res.data;
		});
	};
	
	this.selectAllVisibleBuildingsWithPercentTo50 = function() {
		tmp = this;		
		this.clearSelections();	
		
		angular.forEach(this.visibleBuildings, function(data, index){	
			if (data.percent <= 50){
				data.building_selected = true;
			}
		});		
	};
	
	this.selectAllVisibleBuildingsWithPercentBetween50to75 = function() {
		tmp = this;		
		this.clearSelections();	

		angular.forEach(this.visibleBuildings, function(data, index){	
			if (data.percent > 50 && data.percent < 75 ){
				data.building_selected = true;
			}
		});			
	};
	
	this.selectAllVisibleBuildingsWithPercentAbove75 = function() {
		tmp = this;		
		this.clearSelections();	
		
		angular.forEach(this.visibleBuildings, function(data, index){	
			if (data.percent >= 75 ){
				data.building_selected = true;
			}
		});				
	};	
	
	this.TotalBuildingsDebts = function() {
		total_debt = 0;
		tmp = this;				
			
		angular.forEach(this.visibleBuildings, function(data, index){
			if ('total_debt' in data) {
				total_debt+= data.total_debt;
			}
		});			
		return total_debt;
	};
	
	//call server to get all builgings' info
	this.GetBuildings = function(updated_building){	
		//'this' inside the scope of success function will point to $http, so we store the controller pointer into tmp		
		tmp = this;		
		tmp.loading = true; 
		tmp.masterCheckBoxState = 1;
		tmp.clearSelections();
	
		$http.get('/fetchBuildingsDebts', {
		params: {
			start_date: $filter('date')(tmp.user.start_dt, 'yyyy-MM-dd' ),
			end_date: $filter('date')(tmp.user.finish_dt, 'yyyy-MM-dd'),
			updated_building: updated_building,
			debt_type: tmp.user.debt_type
			
		}
		}).success(function(data) {										
			tmp.UpdateBuildings(_.values(data));				
		});
	};
	
	this.progressBarClass = function(percent) {
		if (percent >= 75) {
			return 'progress-bar-success';
		}
		else if (percent > 50) {
			return 'progress-bar-warning';
		}
		
		else {
			return 'progress-bar-danger';
		}
	};
	//call server to update building's database
	this.UpdateDataBase = function(row, refresh){	
		element_id = row.id;
		//'this' inside the scope of success function will point to $http, so we store the controller pointer into tmp
		tmp = this;		
		
		//need to serialize data in angular (http://stackoverflow.com/questions/12190166/angularjs-any-way-for-http-post-to-send-request-parameters-instead-of-json)
		//as a best practice do it also when sending ajax requests via jquery
		tmp.loading = true;
		row.loading = true;
		
		// or To globally override the default transforms, override the $httpProvider.defaults.transformRequest and $httpProvider.defaults.transformResponse properties of the $httpProvider. as suggested in http://victorblog.com/2012/12/20/make-angularjs-http-service-behave-like-jquery-ajax/
		$http.post('/updateBuilding', 
			$.param(
				{'element_id': element_id}
			)).success(function(data) {
				if (refresh) {
					tmp.GetBuildings(data.new_building_id);	
				}
				tmp.loading = false;
				row.loading = false;
			}).error(function(data) {
				console.log('response: ',data);
			});
			
			
	};	
	
	this.sendMail = function(building_type) {
		chosenBuildings = [];
		
		$.each(this.elements, function(index, data){				
			if (data.building_selected) {
				if (building_type.length) {
					chosenBuildings.push('building_'+building_type+'-'+data.id);				
				}
				else {
					chosenBuildings.push('building-'+data.id);	
				}
			}
		});	
				
		$location.url( '/group_mail?entities='+chosenBuildings);
	};
	
	this.editBuilding = function(building_details) {
		this.showAddForm = true;	
		this.session = building_details;			
	};		
	
	this.addNewBuilding = function(){		
		tmp = this;	
		//'this' inside the scope of success function will point to $http, so we store the controller pointer into tmp		
		tmp.loading = true; 
		
		$http.post('/addNewBuilding', 
			$.param({
				building: JSON.stringify(this.session)			
			}
			)).success(function(data) {				
				tmp.loading = false; 
				tmp.showAddForm = false;
				tmp.session = {};	
				tmp.GetBuildings(data.id);				
		});		
	};
	
	this.deleteBuildings = function(building_id) {
		if (confirm('פעולה זו תמחק את כל נתוני הבניינים, הדיירים וקריאות השירות המשוייכות אליהם. חשוב לציין כי פעולה זו לא תמחוק את קבצי האקסל המייצגים את הבניינים ובפעם הבאה שהמערכת תעלה, הקבצים יימצאו והבניינים יוכנסו מחדש למערכת') ) {
			tmp = this;
			chosenBuildings = [];
			
			if (building_id) {				
				chosenBuildings = [building_id];
			}
			else {
				$.each(this.elements, function(index, data){				
					if (data.building_selected) {				
						chosenBuildings.push(data.id);								
					}
				});
			}
				
			tmp.loading = true;
			$http.post('/deleteBuildings', 
			$.param(
				{'building_ids': JSON.stringify(chosenBuildings)}
			)).success(function(data) {				
				tmp.loading = false;
				tmp.GetBuildings();
			}).error(function(data) {
				console.log('response: ',data);
			});
		}
							
	};
	
	this.sendSms = function(building_type) {
		chosenBuildings = [];
		
		$.each(this.elements, function(index, data){				
			if (data.building_selected) {
				if (building_type.length) {
					chosenBuildings.push('building_'+building_type+'-'+data.id);				
				}
				else {
					chosenBuildings.push('building-'+data.id);	
				}
			}
		});	
				
		$location.url( '/group_sms?entities='+chosenBuildings);
	};
	
	this.UpdateBuildingsDataBase = function(building_type) {
		tmp = this;
		
		$.each(this.elements, function(index, data){				
			if (data.building_selected) {			
				tmp.UpdateDataBase(data, true)
			}				
		});			
	};
	
	this.CreateBuildingsServiceRequest = function() {
		tmp = this;		
		$.each(this.elements, function(index, data){				
			if (data.building_selected) {			
				tmp.OpenServiceRequest(data);
			}				
		});							
	};
	
	this.OpenServiceRequest = function(row) {
		tmp = this;
		$location.url( '/service?buildingId='+row.id);
		
	};		
	
	this.DownloadBuildingFiles = function(row) {
		$http.get('/get_building_files', {
		params: {
			building_id: row.id			
		}
		}).success(function(data) {						
			tmp.building_files = data.building_files;						
		});
	};
	
	this.CreateUrl = function(building_file){		
		return '/downloads/' + building_file;
	};
	
	if (_.isUndefined(this.user.debt_types)) {
		this.GetDebtTypes();
		//this.user.debt_type = '1';
	}
	else {
		this.GetBuildings($routeParams.buildingId);	
	}
	//this.GetBuildings($routeParams.buildingId);	
	
}]);	