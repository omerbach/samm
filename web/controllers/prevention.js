		
angular.module('sam').controller('preventionController', ['$scope', '$filter','$http','$log', '$location','$compile', '$routeParams', '$modal', 'User', 'ngTableParams', function($scope, $filter, $http, $log, $location, $compile, $routeParams, $modal, User, ngTableParams) {
	
	this.availablePreventions = [];	
	
	tmp = this;
	//a factory which passes parameters cross controllers
	this.user = User;	

	this.maximum_records = 0;
	this.limit = 25;

	this.buildingData = "";
	this.categoryData = "";
	this.professionalData = "";
	this.preventionData = "";
		
	this.showAddForm = false;
	this.loading = false;	

	this.column_id = false;
	this.column_description = true;
	this.column_category = true;
	this.column_building = true;
	this.column_worker = true;
	this.column_professional = true;
	this.column_months = true;
	this.column_comment = true;
	this.column_cost = false;
	
	this.masterCheckBoxState = 1; //1- uncheck, 2-partial, 3-all		
	this.total_preventions = 0;
	this.showColumnPanel = false;

	this.tableParams = new ngTableParams(
		{
			sorting: {description: "asc"}
		},
		{
			counts: [],		
			total: this.availablePreventions.length, // length of data
			getData: function($defer, params) {				
				var orderedData = tmp.orderData(tmp.availablePreventions);

				tmp.availablePreventions = orderedData;
			}
		}
	);
		
	this.orderData = function(data) {
						
		params = this.tableParams;		
		var objectOf = null;
		var key = null;
		var direction = null;
		
		if (params.sorting().building_name) {	
			key = "building_id";
			objectOf = this.buildingOf;
			direction = params.sorting().building_name;
		}
		else if (params.sorting().worker_name) {	
			key = "worker_id";
			objectOf = this.workerOf;
			direction = params.sorting().worker_name;
		}
		else if (params.sorting().professional_name) {	
			key = "professional_id";
			objectOf = this.professionalOf;
			direction = params.sorting().professional_name;
		}
				
		//http://stackoverflow.com/questions/26045390/ng-table-how-to-sort-by-a-value-which-is-not-a-part-of-ng-repeat
		if (key && objectOf && direction) {
			orderedData = data.sort(function(a, b){				
				
				//a key could not exist or point to non existing object (for example a building which were deleted)
				var nameA = a[key] == "" || _.isUndefined(objectOf[a[key]]) ? "" : objectOf[a[key]].name.toLowerCase();
				var nameB = b[key] == "" || _.isUndefined(objectOf[b[key]]) ? "" : objectOf[b[key]].name.toLowerCase();				
				
				if (nameA < nameB)
					return -1;
					
				if (nameA > nameB)
					return 1;
				
				return 0 ;
			});
			
			if (direction == 'desc') {
			  orderedData = orderedData.reverse();
			}
		}
		
		else {
			var orderedData = params.sorting() ?
										$filter('orderBy')(data, params.orderBy()) :
										data;
		}
		
		return orderedData;
		
	}	
	this.addNewPrevention = function(){
		tmp = this;	
		//'this' inside the scope of success function will point to $http, so we store the controller pointer into tmp		
		tmp.loading = true; 
		
            $http.post('/addNewPrevention',
			$.param({
				prevention: JSON.stringify(this.session)
			}
			)).success(function(data) {				
				tmp.loading = false; 
				tmp.showAddForm = false;
				tmp.reset_session();
				tmp.GetPreventions(data.prevention_id);
		});
	};

	this.ClearBuilding = function(){	
		this.session.building_id = null;		
	};
	
	this.AutoCompleteChange = function(val) {				
		if(val == "") {
			this.GetPreventions();
		}						
	};

	this.GetBuildings = function(){
		tmp = this;			
		tmp.loading = true;
		
		$http.get('/fetchBuildingsGeneral', {
		}).success(function(data) {
		        tmp.buildingOf = data;
				tmp.availableBuildings = _.values(data);
				tmp.loading = false;				
		});
	};

	this.isLoading = function() {
		if (this.loading) {
			return "fa-spin";
		}
	};

	this.masterCheckBoxClick = function($event){		
		if (this.masterCheckBoxState == 1){			
			this.selectAll();
		}
		else if (this.masterCheckBoxState == 3){			
			this.clearSelections();	
		}
		else if (this.masterCheckBoxState == 2){			
			this.clearSelections();	
		}
		$event.stopPropagation();		
	};
	
	this.clearSelections = function(){											
		tmp = this;
		angular.forEach(this.availablePreventions, function(data, index){							
			data.prevention_selected = false;
		});
	};
	
	this.selectAll = function(){							
		tmp = this;
		this.clearSelections();		
		angular.forEach(this.availablePreventions, function(data, index){							
			data.prevention_selected = true;
		});
	};
	
	this.guessBuildingName = function(val) {		
		return $http.get('/guessBuilding', {
			params: {
			name: val
			}
		}).then(function(res) {		
			return res.data;
		});
	};

	this.guessPreventionName = function(val) {
		return $http.get('/guessPrevention', {
			params: {
			name: val
			}
		}).then(function(res) {
			return res.data;
		});
	};
	
	//call server to get all professionals' info
	this.GetProfessionals = function(updated_professional){		
		//'this' inside the scope of success function will point to $http, so we store the controller pointer into tmp		
		tmp = this;			
		tmp.loading = true; 
		//http://stackoverflow.com/questions/17225088/http-get-parameters-does-not-work
		$http.get('/fetchProfessionals', {
		params: {		
			updated_professional: updated_professional
		}
		}).success(function(data) {						
			tmp.professionalOf = data.professionals;
			tmp.availableProfessionals = _.values(tmp.professionalOf);						
			tmp.loading = false;						
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
	
	this.UpdatePreventionsMetaData = function(delta) {
		this.total_preventions += delta;
		if (!this.total_preventions) {
				this.masterCheckBoxState = 1;
			}
		else if (this.total_preventions == _.keys(preventions_data).length) {
			this.masterCheckBoxState = 3;
		}
		else {
			this.masterCheckBoxState = 2;
		}						
	};		
	
	this.UpdatePreventions = function(new_preventions) {
		tmp = this;				
		tmp.total_preventions = 0;
		preventions_data = tmp.orderData(new_preventions);		
		
		//remove previous watches
		angular.forEach(tmp.availablePreventions, function(prevention, index){
			prevention['listener']();
		});								
		
		angular.forEach(preventions_data, function(prevention, index){
			//when fetching the preventions_data, each row which is selected from the beginning will not
			if (preventions_data[index].prevention_selected) {				
				tmp.UpdatePreventionsMetaData(1);
			}

			//add watchers for all preventions to track changes in row selections (this is due to the fact that angular does not 
			//trigget on change methods when model is changed)				
			listener = $scope.$watch(
			//watchExpression
			function(){
				return preventions_data[index];
			}, 
			//listener
			function(nv, ov) {				
				//row check box has changed
				if (nv.prevention_selected != ov.prevention_selected) {
					//update total of preventions selected
					delta = 1;
					if (!nv.prevention_selected) {
						delta *= -1;
					}		
					
					tmp.UpdatePreventionsMetaData(delta);
				}
			},
			//objectEquality
			true);	
			
			//http://stackoverflow.com/questions/14957614/angular-js-clear-watch
			//store the return value from each watch. this is the function which deregister the object
			prevention['listener'] = listener;
		});
		
		tmp.availablePreventions = preventions_data;
		tmp.loading = false;
	}

	
	//call server to get all prevention Requests' info
	this.GetPreventions = function(prevention_id, building_id_input, worker_id_input, professional_id_input, showmore){

		if (!showmore) {
			this.limit = 25;
		}
		//'this' inside the scope of success function will point to $http, so we store the controller pointer into tmp		
		tmp = this;		
		
		tmp.masterCheckBoxState = 1;		
		tmp.loading = true; 
		tmp.clearSelections();

		//http://stackoverflow.com/questions/17225088/http-get-parameters-does-not-work
		$http.get('/fetchPreventions', {
		params: {
			updated_prevention_id: prevention_id,
			building_id: tmp.buildingData.id,
			professional_id: tmp.professionalData.id,
			description: tmp.preventionData.id,
			limit: tmp.limit
		}
		}).success(function(data) {					
			tmp.maximum_records = data.maximum_records;
			tmp.UpdatePreventions(_.values(data.preventions));
			
			edit = false;
			if (!_.isUndefined(building_id_input) && building_id_input.length) {				
				tmp.session.building_id = building_id_input;
				edit = true;
			}

			if (!_.isUndefined(worker_id_input) && worker_id_input.length) {				
				tmp.session.worker_id = worker_id_input;
				edit = true;
			}
			
			if (!_.isUndefined(professional_id_input) && professional_id_input.length) {				
				tmp.session.professional_id = professional_id_input;
				edit = true;
			}
			
			if (edit == true) {				
				tmp.showAddForm = true;
			}
			else {
				tmp.showAddForm = false;
			}
			
		});
				
		
	};

	this.ClonePrevention = function() {
		tmp = this;

        $http.get('/fetchDistinctPreventionNames', {
		params: {}
		}).success(function(distinct_preventions) {
		    var modalInstance = $modal.open({
              templateUrl: 'myCopyBuildingModalContent.html',
              controller: 'myCopyBuildingCtrl',
              resolve: {
                availablePreventions: function () {
                  return distinct_preventions;
                },
                availableBuildings: function () {
                  return tmp.availableBuildings;
                }
              }
            });

            modalInstance.result.then(function (res) {
                tmp.loading = true;

                target_building = res.target_building;
                source_preventions = res.source_preventions;

                $http.post('/bulkPreventions',
                    $.param({
                        preventions: JSON.stringify(source_preventions),
                        target_building: target_building
                    }
                    )).success(function(data) {
                        tmp.buildingData = {"id": target_building, "name": tmp.buildingOf[target_building].name};
                        tmp.loading = false;
                        tmp.showAddForm = false;
                        tmp.reset_session();
                        tmp.GetPreventions();
                });
            }, function () {
              $log.info('Modal dismissed at: ' + new Date());
            });
		});

	};
	
	this.editPrevention = function(prevention_details) {
		this.showAddForm = true;
		this.session = prevention_details;	
		this.session.status = String(this.session.status);
		
		this.session.edit = true;
	};

	this.deletePreventions = function(row) {

		if (confirm('אשר מחיקת טיפול') ) {
			tmp = this;
			chosenPreventions = [];
			linkedServices = false;
			
			if (row) {
			    prevention_id = row.prevention_id;
				chosenPreventions = [prevention_id];

				if (row.linked_services) {
                    linkedServices = true;
                }
			}
			else {				
				$.each(this.availablePreventions, function(index, data){				
					if (data.prevention_selected) {
						chosenPreventions.push(data.prevention_id);
					}
					if (data.linked_services) {
                        linkedServices = true;
                    }
				});
			}

			tmp.deleteServicePreventionPopUp(chosenPreventions, linkedServices);
		}
							
	};

	this.deleteServicePreventionPopUp = function (chosenServices, linkedServices) {

		tmp = this;
        if (linkedServices) {
            var modalInstance = $modal.open({
              templateUrl: 'myServicePreventionModalContent.html',
              controller: 'servicePreventionModalCtrl',
              resolve: {}
            });

            modalInstance.result.then(function (delete_status) {
                tmp.deletePreventionRequestsFromServer(chosenPreventions, delete_status);
            }, function () {
              tmp.delete_status = -1;
              $log.info('Modal dismissed at: ' + new Date());
            });

         }
         else {
            tmp.deletePreventionRequestsFromServer(chosenPreventions, 0);
         }
	};

	this.deletePreventionRequestsFromServer = function(chosenPreventions, delete_status) {
        tmp.loading = true;
        $http.post('/deletePreventions',
        $.param(
            {
                'prevention_ids': JSON.stringify(chosenPreventions),
                'delete_status': delete_status
            }
        )).success(function(data) {
            tmp.loading = false;
            tmp.GetPreventions();
        }).error(function(data) {
            console.log('response: ',data);
        });
	};

	// Any function returning a promise object can be used to load values asynchronously
	this.guessBuildingName = function(val) {		
		return $http.get('/guessBuilding', {
			params: {
			name: val
			}
		}).then(function(res) {		
			return res.data;
		});
	};
	
	// Any function returning a promise object can be used to load values asynchronously
	this.guessProfessional = function(val) {		
		return $http.get('/guessProfessional', {
			params: {
			name: val
			}
		}).then(function(res) {		
			return res.data;
		});
	};

	this.MultiTypeElements = function(){
		tmp = this;			
		tmp.loading = true;
		
		$http.get('/fetchMultiTypeElements', {
		params: {		
			include_specific_buildings: true			
		}
		}).success(function(data) {	
				tmp.entities = data.entities;				
				tmp.loading = false;				
		});
	};
	
	this.guessCategory = function(val) {
		return $http.get('/guessServiceCategory', {
			params: {
			name: val
			}
		}).then(function(res) {		
			return res.data;
		});
	};

	this.reset_session = function() {
		this.session = {
		"january": false,
	    "february": false,
	    "march": false,
	    "april": false,
	    "may": false,
	    "june": false,
	    "july": false,
	    "august": false,
	    "september": false,
	    "october": false,
	    "november": false,
	    "december": false};
	};

	this.toStr = function(val) {
		if (_.isUndefined(val) || _.isNull(val)) {
			return "";
		}
		return val.toString();
	};

	this.updateAllMonths = function(record) {
	    val = record.all_months;
	    record.january = val;
	    record.february = val;
	    record.march = val;
	    record.april = val;
	    record.may = val;
	    record.june = val;
	    record.july = val;
	    record.august = val;
	    record.september = val;
	    record.october = val;
	    record.november = val;
	    record.december = val;
	};

	this.atLeastOneMonthChosen = function(record){

	    if (record) {
	        return record.january || record.february || record.march || record.april || record.may || record.june || record.july || record.august || record.september || record.october || record.november || record.december ;
	    }
	    return false;
	};

    //implementing the disabling myself as select2 doesn't work with $invalid
	this.partialyData = function() {

		tmp = this;
		basicFieldExists =  this.atLeastOneMonthChosen(tmp.session) && tmp.toStr(tmp.session.building_id).length > 0 && tmp.toStr(tmp.session.description).length > 0;
		return !basicFieldExists;
	};
	
	this.reset_session();	
	this.GetBuildings();
	this.GetProfessionals();
	this.GetWorkers();
	this.GetPreventions(0, $routeParams.buildingId, $routeParams.workerId, $routeParams.professionalId);
	this.MultiTypeElements();
}]);

angular.module('sam').controller('servicePreventionModalCtrl', ['$scope', '$modalInstance', function($scope, $modalInstance) {

	$scope.ok = function (delete_status) {
		$modalInstance.close(delete_status);
	};

	$scope.cancel = function () {
		$modalInstance.dismiss('cancel');
	};
}]);

angular.module('sam').controller('myCopyBuildingCtrl', ['$scope', '$modalInstance', '$http', 'availablePreventions','availableBuildings', function($scope, $modalInstance, $http, availablePreventions, allBuildings) {

    tmp = this;

    $scope.filterOptions = {
		filterText: ""
	};
	$scope.availablePreventions = availablePreventions;
	$scope.allBuildings = allBuildings;

	$scope.ok = function (target_building) {

	    source_preventions = [];
	    angular.forEach($scope.availablePreventions, function(prev, index) {
	        if (prev.copy_prevention_selected) {
	            source_preventions.push(prev);
	        }
	    });

		$modalInstance.close({'target_building': target_building.id, 'source_preventions': source_preventions});
	};

	$scope.cancel = function () {
		$modalInstance.dismiss('cancel');
	};

    /*
	$scope.tenant_changed = function (tenant_obj, alert_obj) {
		if (tenant_obj && alert_obj) {
			template_details = {
				'appartment': tenant_obj.apartment_number,
				'totalDebt': tenant_obj.total_debt,
				'months': tenant_obj.months,
				'building': tenant_obj.name,
				'tenant_name': tenant_obj.tenant_name,
				'payment': tenant_obj.monthly_payment,
				'description': tenant_obj.debt_description
			};

			angular.forEach($scope.dynamic_fields, function(dynamic_field, index){
				template_details[dynamic_field.template_name] = tenant_obj[dynamic_field.template_name];
			});

			$http.get('/parseAlertTemplate', {
			params: {
				path: $scope.template.path,
				details: JSON.stringify(template_details),
				alert: alert_obj.alert_type,
				content: $scope.template[alert_obj.alert_type+'_content'],
				mail_subject: $scope.template.mail_subject

			}
			}).success(function(data) {
				$scope.alert_content = data;
			}).
			error(function(data) {
				$log.log('error!');
				$scope.alert_content = {meta: "שגיאה בתבנית", content: '<div style="background: rgb(207, 33, 33); color: white;font-size: 25px;"><p><i class="fa fa-warning"></i></p><p>נמצאה בעיה בתבנית</p><p>אנא בדקו את תוכן התבנית</p><p>ובצעו את השינויים ההכרחיים</p></div>'};
			});
		}
		else {
			$scope.alert_content = {meta: "", content: ""};
		}
	};*/

}]);


